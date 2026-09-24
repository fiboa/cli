"""Tests for the WFS paging mixin.

The page list is derived from the number of features the server reports, so
these tests answer the hits request with a fake service and check the pages.
"""

from urllib.parse import parse_qs, urlsplit

import pytest

from fiboa_cli.conversion.converter_wfs import WFSConverterMixin
from fiboa_cli.conversion.fiboa_converter import FiboaBaseConverter

BASE_URL = "https://example.test/geoserver/wfs"


class WFSConverter(WFSConverterMixin, FiboaBaseConverter):
    id = "test_wfs"
    wfs_url = BASE_URL
    wfs_params = {"typeNames": "lpis:Parcels", "sortBy": "lpis:id"}
    wfs_page_size = 2
    columns = {"geometry": "geometry", "id": "id"}


class VariantConverter(WFSConverter):
    variants = {"2025": "2025", "2024": "2024"}
    wfs_extension = "json"

    def get_wfs_params(self):
        return {"typeNames": f"lpis:Parcels_{self.variant}", "outputFormat": "application/json"}


class FakeService:
    """Answers the hits request with `body` and records its parameters."""

    def __init__(self, body):
        self.body = body
        self.requests = []

    def get(self, url, params=None, **kwargs):
        self.requests.append(params)
        body = self.body

        class Response:
            text = body
            url = BASE_URL

            def raise_for_status(self):
                pass

        return Response()


def _hits(total, attribute="numberMatched"):
    return f'<wfs:FeatureCollection {attribute}="{total}" numberReturned="0"/>'


@pytest.fixture(autouse=True)
def _rebind_logger():
    """LoggerMixin binds its sink to sys.stdout once per process; a converter
    built here would bind it to this test's capture and mute every later test."""
    yield
    from vecorel_cli.cli.logger import LoggerMixin

    LoggerMixin.logger = None


def _serve(monkeypatch, body):
    fake = FakeService(body)
    monkeypatch.setattr("fiboa_cli.conversion.converter_wfs.requests.get", fake.get)
    return fake


def _query(url):
    return {k: v[0] for k, v in parse_qs(urlsplit(url).query).items()}


def test_pages_cover_the_layer(monkeypatch):
    service = _serve(monkeypatch, _hits(5))
    urls = WFSConverter().get_urls()

    assert service.requests == [
        {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeNames": "lpis:Parcels",
            "sortBy": "lpis:id",
            "resultType": "hits",
        }
    ]
    assert list(urls.values()) == ["test_wfs_0.gml", "test_wfs_2.gml", "test_wfs_4.gml"]
    queries = [_query(url) for url in urls]
    assert [q["startIndex"] for q in queries] == ["0", "2", "4"]
    for query in queries:
        assert query["count"] == "2"
        assert query["typeNames"] == "lpis:Parcels"
        assert query["sortBy"] == "lpis:id"
        assert "resultType" not in query
        assert "maxFeatures" not in query


def test_variant_names_query_and_pages(monkeypatch):
    _serve(monkeypatch, _hits(3))
    converter = VariantConverter()
    converter.select_variant("2024")
    urls = converter.get_urls()

    assert list(urls.values()) == ["test_wfs_2024_0.json", "test_wfs_2024_2.json"]
    assert all(_query(url)["typeNames"] == "lpis:Parcels_2024" for url in urls)


def test_file_names_can_be_overridden(monkeypatch):
    class PaddedConverter(WFSConverter):
        def get_wfs_file_name(self, start):
            return f"page_{start:04d}.gml"

    _serve(monkeypatch, _hits(3))
    urls = PaddedConverter().get_urls()

    assert list(urls.values()) == ["page_0000.gml", "page_0002.gml"]
    assert [_query(url)["startIndex"] for url in urls] == ["0", "2"]


def test_wfs_1_pages_with_max_features(monkeypatch):
    class WFS1Converter(WFSConverter):
        wfs_version = "1.1.0"

    _serve(monkeypatch, _hits(3, "numberOfFeatures"))
    urls = WFS1Converter().get_urls()

    assert len(urls) == 2
    for url in urls:
        query = _query(url)
        assert query["version"] == "1.1.0"
        assert query["maxFeatures"] == "2"
        assert "count" not in query


def test_empty_layer_has_no_pages(monkeypatch):
    _serve(monkeypatch, _hits(0))
    assert WFSConverter().get_urls() == {}


def test_unknown_total_fails(monkeypatch):
    # WFS 2.0 allows a server to answer numberMatched="unknown"
    _serve(monkeypatch, _hits("unknown"))
    with pytest.raises(ValueError, match="get_wfs_total"):
        WFSConverter().get_urls()
