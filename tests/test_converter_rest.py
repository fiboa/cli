"""Tests for the Esri REST paging mixin.

Every page the mixin fetches is a file in the cache, and the bugs it has had
were invisible in the output: pages of one service overwriting another's,
the converter's own `where` being dropped, an error page kept as if it held
data. These tests serve a small fake service so the paging can be watched.
"""

import json
import os
import re

import geopandas as gpd
import pytest
from shapely.geometry import Point

from fiboa_cli.conversion.converter_rest import EsriRESTConverterMixin
from fiboa_cli.conversion.fiboa_converter import FiboaBaseConverter

BASE_URL = "https://example.test/arcgis/rest/services/SIXPAC_2024/MapServer"
SERVICE = "SIXPAC_2024_MapServer"
LAYER_ID = 2
PAGE_SIZE = 2
# the fake layer: five features with ids 1..5, so the last window holds one
FEATURE_IDS = [1, 2, 3, 4, 5]


class RESTConverter(EsriRESTConverterMixin, FiboaBaseConverter):
    id = "test_rest"
    rest_base_url = BASE_URL
    columns = {"geometry": "geometry", "OBJECTID": "id"}


def _feature(oid, key="OBJECTID"):
    return {
        "type": "Feature",
        "properties": {key: oid},
        "geometry": {"type": "Point", "coordinates": [oid, oid]},
    }


def _collection(oids, key="OBJECTID"):
    return {"type": "FeatureCollection", "features": [_feature(o, key) for o in oids]}


class FakeService:
    """Answers the three metadata calls and records every page request."""

    def __init__(self, key="OBJECTID", ids=FEATURE_IDS, page_size=PAGE_SIZE):
        self.key = key
        self.ids = ids
        self.page_size = page_size
        self.pages = []  # the `where` of every page the mixin downloaded

    def get(self, url, params=None, **kwargs):
        params = params or {}

        class Response:
            def __init__(self, payload):
                self._payload = payload

            def json(self):
                return self._payload

        if params.get("f") == "pjson":
            if url.endswith(f"/{LAYER_ID}"):  # the layer's fields name the real key
                return Response({"fields": [{"name": self.key}, {"name": "USO_SIGPAC"}]})
            return Response(
                {
                    "layers": [{"id": LAYER_ID, "name": "Recintos"}],
                    "maxRecordCount": self.page_size,
                }
            )
        floor = int(re.search(r">(-?\d+)", params["where"]).group(1))
        above = [o for o in self.ids if o > floor]
        bound = max(above) if params["orderByFields"].endswith("DESC") else min(above)
        return Response({"features": [{"attributes": {self.key: bound}}]})

    def stream(self, _source_fs, url, file):
        where = url.split("where=")[1].split("&")[0]
        self.pages.append(where)
        # the clause is "<attr>>lo AND <attr><=hi", optionally followed by the
        # converter's own filter
        lo = int(where.split("%3E")[1].split("+")[0])
        hi = int(where.split("%3C%3D")[1].split("+")[0])
        oids = [o for o in self.ids if lo < o <= hi]
        file.write(json.dumps(_collection(oids, self.key)).encode("utf-8"))


@pytest.fixture(autouse=True)
def _rebind_logger():
    """LoggerMixin binds its sink to sys.stdout once per process; a converter
    built here would bind it to this test's capture and mute every later test."""
    yield
    from vecorel_cli.cli.logger import LoggerMixin

    LoggerMixin.logger = None


@pytest.fixture(autouse=True)
def _no_backoff(monkeypatch):
    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.time.sleep", lambda _s: None)


@pytest.fixture
def service(monkeypatch):
    fake = FakeService()
    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.requests.get", fake.get)
    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.stream_file", fake.stream)
    return fake


def _read(converter, cache, service=None):
    converter.cache_folder = str(cache)
    return list(converter.get_data([BASE_URL]))


def test_pages_by_id_window_and_caches_per_service(service, tmp_path):
    converter = RESTConverter()
    pages = _read(converter, tmp_path)

    assert [len(data) for data, *_ in pages] == [2, 2, 1]
    assert all(rest == [BASE_URL, BASE_URL, LAYER_ID] for _, *rest in pages)
    # the window is half-open, so no id is fetched twice and none is skipped
    assert service.pages == [
        "OBJECTID%3E0+AND+OBJECTID%3C%3D2",
        "OBJECTID%3E2+AND+OBJECTID%3C%3D4",
        "OBJECTID%3E4+AND+OBJECTID%3C%3D6",
    ]
    # layer ids repeat across services (every SIXPAC_<year> has its Recintos at 2),
    # so the service name has to be part of the file name; the window bounds are
    # in it too, so a page kept under another page size is never misread
    assert sorted(os.listdir(tmp_path)) == [
        f"test_rest_{SERVICE}_{LAYER_ID}_r{lo}-{lo + PAGE_SIZE}.geojson" for lo in (0, 2, 4)
    ]


def test_converter_where_is_kept(service, tmp_path):
    converter = RESTConverter()
    converter.rest_params = {"where": "USO_SIGPAC='TA'"}
    _read(converter, tmp_path)

    # the window clause used to overwrite the converter's own filter
    assert all(page.endswith("+AND+%28USO_SIGPAC%3D%27TA%27%29") for page in service.pages)


def test_qualified_key_field_is_discovered(monkeypatch, tmp_path):
    """A joined layer qualifies every field with its table name; the layer's
    own metadata names them, where a one-row probe would be a query."""
    fake = FakeService(key="RECINTOS.OBJECTID")
    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.requests.get", fake.get)
    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.stream_file", fake.stream)

    _read(RESTConverter(), tmp_path)

    assert all(page.startswith("RECINTOS.OBJECTID%3E") for page in fake.pages)


def test_qualified_fields_lose_their_table_prefix(monkeypatch, tmp_path):
    """A joined layer qualifies every field, so `columns` would match nothing."""
    fake = FakeService(key="RECINTOS.OBJECTID")
    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.requests.get", fake.get)
    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.stream_file", fake.stream)

    pages = _read(RESTConverter(), tmp_path)

    assert all("OBJECTID" in data.columns for data, *_ in pages)
    assert not any("." in column for data, *_ in pages for column in data.columns)


def test_an_unqualified_field_wins_over_a_qualified_one():
    """The geometry table leads, so its plain name is not overwritten."""
    gdf = gpd.GeoDataFrame(
        {"OBJECTID": [1], "ATTR.OBJECTID": [9], "ATTR.USO": ["TA"]},
        geometry=[Point(0, 0)],
    )
    out = EsriRESTConverterMixin._unqualify(gdf)

    assert out["OBJECTID"].tolist() == [1]
    assert out["USO"].tolist() == ["TA"]


def test_error_response_is_not_kept_as_a_page(service, tmp_path, monkeypatch):
    def error_page(_source_fs, url, file):
        file.write(b'{"error":{"code":500,"message":"Internal error"}}')

    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.stream_file", error_page)

    with pytest.raises(RuntimeError, match=r"Could not read ids \(0 ... 2\]"):
        _read(RESTConverter(), tmp_path)
    assert os.listdir(tmp_path) == []


def test_broken_download_is_not_kept_as_a_page(service, tmp_path, monkeypatch):
    def broken(_source_fs, url, file):
        file.write(b'{"type":"FeatureColl')
        raise ConnectionError("connection reset")

    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.stream_file", broken)

    with pytest.raises(RuntimeError, match="connection reset"):
        _read(RESTConverter(), tmp_path)
    assert os.listdir(tmp_path) == []


def test_a_page_is_asked_for_again(service, tmp_path, monkeypatch):
    """Hundreds of pages per edition: one refusal is normal, not fatal."""
    attempts = []
    real = service.stream

    def flaky(source_fs, url, file):
        attempts.append(url)
        if len(attempts) == 1:
            file.write(b'{"type":"FeatureColl')
            raise ConnectionError("connection reset")
        return real(source_fs, url, file)

    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.stream_file", flaky)

    pages = _read(RESTConverter(), tmp_path)

    assert [len(data) for data, *_ in pages] == [2, 2, 1]
    assert len(attempts) == 4  # three pages, the first of them twice


def test_service_metadata_is_asked_for_again(service, tmp_path, monkeypatch):
    """Esri answers a failed request with 200 and an error body."""
    answers = [{"error": {"code": 502, "message": "Bad Gateway"}}]
    real = service.get

    def tired(url, params=None, **kwargs):
        if answers:
            payload = answers.pop(0)
            return type("Response", (), {"json": lambda self: payload})()
        return real(url, params, **kwargs)

    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.requests.get", tired)

    pages = _read(RESTConverter(), tmp_path)

    assert [len(data) for data, *_ in pages] == [2, 2, 1]
    assert answers == []


def test_pages_cached_under_the_old_sorted_scheme_are_not_reused(service, tmp_path):
    """The old file name carries neither service nor filter, so nothing proves
    where its rows came from; such pages are fetched again under the new key."""
    legacy = tmp_path / f"test_rest_{LAYER_ID}_-1.geojson"
    legacy.write_text(json.dumps(_collection([1, 2])))

    pages = _read(RESTConverter(), tmp_path)

    assert [len(data) for data, *_ in pages] == [2, 2, 1]
    assert len(service.pages) == 3  # every window was fetched


def test_pages_of_one_filter_do_not_serve_another(service, tmp_path):
    """de_st selects its edition by `where` alone, on one service and one layer."""
    first = RESTConverter()
    first.rest_params = {"where": "ID_VERSIONID='2023.1'"}
    _read(first, tmp_path)
    second = RESTConverter()
    second.rest_params = {"where": "ID_VERSIONID='2021.1'"}
    _read(second, tmp_path)

    assert len(service.pages) == 6  # no page of the first edition served the second


def test_pages_kept_under_another_page_size_still_cover_everything(monkeypatch, tmp_path):
    """maxRecordCount follows the service's configuration. The file name carries
    the window it was fetched for, so after a size change a kept page is either
    followed at its own bounds or ignored — never misread as a wider window."""
    small = FakeService(page_size=2)
    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.requests.get", small.get)
    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.stream_file", small.stream)
    _read(RESTConverter(), tmp_path)

    big = FakeService(page_size=3)
    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.requests.get", big.get)
    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.stream_file", big.stream)
    pages = _read(RESTConverter(), tmp_path)

    assert big.pages == []  # the kept windows still cover the layer completely
    assert sorted(o for data, *_ in pages for o in data["OBJECTID"]) == FEATURE_IDS


def test_a_wide_id_gap_is_walked_once_and_cached(monkeypatch, tmp_path):
    """Two rows at ids 1 and 10001: the gap between them costs one empty page
    and one bound query, not five thousand page downloads."""
    fake = FakeService(ids=[1, 10001])
    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.requests.get", fake.get)
    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.stream_file", fake.stream)

    pages = _read(RESTConverter(), tmp_path)

    assert [len(data) for data, *_ in pages] == [1, 1]
    assert len(fake.pages) == 3  # (0,2], the empty (2,4] widened to (2,10000], (10000,10002]

    assert [len(data) for data, *_ in _read(RESTConverter(), tmp_path)] == [1, 1]
    assert len(fake.pages) == 3  # the second run was answered by the cache alone


def test_empty_window_is_skipped(monkeypatch, tmp_path):
    """An id gap wider than a page yields a window with nothing in it."""
    fake = FakeService(ids=[1, 6])
    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.requests.get", fake.get)
    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.stream_file", fake.stream)

    pages = _read(RESTConverter(), tmp_path)

    assert [len(data) for data, *_ in pages] == [1, 1]
    assert len(fake.pages) == 3  # the middle window was fetched, and held nothing


def test_get_urls_requires_a_base_url():
    class NoURL(EsriRESTConverterMixin, FiboaBaseConverter):
        id = "no_url"
        columns = {"geometry": "geometry", "id": "id"}

    assert RESTConverter().get_urls() == {"REST": BASE_URL}
    with pytest.raises(AssertionError, match="rest_base_url"):
        NoURL().get_urls()


def test_a_variant_may_name_its_own_service():
    """An edition can live in a service of its own (es_ib's historic layers)."""
    other = "https://example.test/arcgis/rest/services/HISTORIC/MapServer"

    class TwoServices(RESTConverter):
        variants = {"2026": BASE_URL, "2024": other}

    assert TwoServices().get_urls() == {"REST": BASE_URL}  # the first variant
    converter = TwoServices()
    converter.variant = "2024"
    assert converter.get_urls() == {"REST": other}


def test_a_variant_that_is_not_a_url_leaves_the_base_url_alone():
    class Years(RESTConverter):
        variants = {"2024": "2024"}

    converter = Years()
    converter.variant = "2024"
    assert converter.get_urls() == {"REST": BASE_URL}


def test_id_bound_is_retried(monkeypatch):
    """The one sorted query left is the one a tired server gives up on."""

    class Answer:
        def json(self):
            return {"features": [{"attributes": {"OBJECTID": 7}}]}

    answers = [RuntimeError("502"), Answer()]

    def get(url, params=None, **kwargs):
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.requests.get", get)

    assert RESTConverter()._rest_id_bound("url", "OBJECTID", None, "ASC") == 7
    assert answers == []


def test_download_files_passes_the_rest_url_through(tmp_path):
    converter = RESTConverter()
    assert converter.download_files({"REST": BASE_URL}, str(tmp_path)) == [BASE_URL]
    assert converter.cache_folder == str(tmp_path)
