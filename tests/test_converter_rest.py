"""Tests for the Esri REST paging mixin.

Every page the mixin fetches is a file in the cache, and the bugs it has had
were invisible in the output: pages of one service overwriting another's,
the converter's own `where` being dropped, an error page kept as if it held
data. These tests serve a small fake service so the paging can be watched.
"""

import json
import os

import pytest

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

    def __init__(self, key="OBJECTID", ids=FEATURE_IDS):
        self.key = key
        self.ids = ids
        self.pages = []  # the `where` of every page the mixin downloaded

    def get(self, url, params=None, **kwargs):
        params = params or {}

        class Response:
            def __init__(self, payload):
                self._payload = payload

            def json(self):
                return self._payload

        if params.get("f") == "pjson":
            return Response(
                {"layers": [{"id": LAYER_ID, "name": "Recintos"}], "maxRecordCount": PAGE_SIZE}
            )
        if params.get("outFields") == "*":  # the probe for the real key field
            return Response({"features": [{"attributes": {self.key: self.ids[0]}}]})
        bound = max(self.ids) if params["orderByFields"].endswith("DESC") else min(self.ids)
        return Response({"features": [{"attributes": {self.key: bound}}]})

    def stream(self, _source_fs, url, file):
        where = url.split("where=")[1].split("&")[0]
        self.pages.append(where)
        lo, hi = (int(n) for n in (where.split("%3E")[1].split("+")[0], where.split("%3C%3D")[1]))
        oids = [o for o in self.ids if lo < o <= hi]
        file.write(json.dumps(_collection(oids, self.key)).encode("utf-8"))


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
    # so the service name has to be part of the file name
    assert sorted(os.listdir(tmp_path)) == [
        f"test_rest_{SERVICE}_{LAYER_ID}_r{lo}.geojson" for lo in (0, 2, 4)
    ]


def test_converter_where_is_kept(service, tmp_path):
    converter = RESTConverter()
    converter.rest_params = {"where": "USO_SIGPAC='TA'"}
    _read(converter, tmp_path)

    # the window clause used to overwrite the converter's own filter
    assert all(page.startswith("%28USO_SIGPAC%3D%27TA%27%29+AND+") for page in service.pages)


def test_qualified_key_field_is_discovered(monkeypatch, tmp_path):
    """A joined layer qualifies every field with its table name."""
    fake = FakeService(key="RECINTOS.OBJECTID")
    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.requests.get", fake.get)
    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.stream_file", fake.stream)

    _read(RESTConverter(), tmp_path)

    assert all(page.startswith("RECINTOS.OBJECTID%3E") for page in fake.pages)


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

    with pytest.raises(ConnectionError):
        _read(RESTConverter(), tmp_path)
    assert os.listdir(tmp_path) == []


def test_legacy_page_is_reused_when_its_ids_cover_the_window(service, tmp_path):
    """Pages cached by the old sorted paging are keyed by the previous page's
    last id; a dense one covers exactly the window that replaced it."""
    legacy = tmp_path / f"test_rest_{LAYER_ID}_-1.geojson"
    legacy.write_text(json.dumps(_collection([1, 2])))

    pages = _read(RESTConverter(), tmp_path)

    assert [len(data) for data, *_ in pages] == [2, 2, 1]
    assert service.pages == [  # the first window came from the legacy file
        "OBJECTID%3E2+AND+OBJECTID%3C%3D4",
        "OBJECTID%3E4+AND+OBJECTID%3C%3D6",
    ]


def test_legacy_page_that_does_not_cover_the_window_is_ignored(service, tmp_path):
    """The old key is the last id of the previous page, which on a layer with
    gaps says nothing about which ids the file holds."""
    gappy = tmp_path / f"test_rest_{LAYER_ID}_-1.geojson"
    gappy.write_text(json.dumps(_collection([1, 3])))
    unreadable = tmp_path / f"test_rest_{LAYER_ID}_2.geojson"
    unreadable.write_text("not geojson at all")

    _read(RESTConverter(), tmp_path)

    assert service.pages == [
        "OBJECTID%3E0+AND+OBJECTID%3C%3D2",
        "OBJECTID%3E2+AND+OBJECTID%3C%3D4",
        "OBJECTID%3E4+AND+OBJECTID%3C%3D6",
    ]


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


def test_download_files_passes_the_rest_url_through(tmp_path):
    converter = RESTConverter()
    assert converter.download_files({"REST": BASE_URL}, str(tmp_path)) == [BASE_URL]
    assert converter.cache_folder == str(tmp_path)
