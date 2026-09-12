"""Tests for the Esri REST paging mixin.

Every page the mixin fetches is a file in the cache, and the bugs it has had
were invisible in the output: pages of one service overwriting another's,
the converter's own `where` being dropped, an error page kept as if it held
data. These tests serve a small fake service so the paging can be watched.
"""

import json
import os

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
            if url.endswith(str(LAYER_ID)):  # the layer's fields name the real key
                return Response({"fields": [{"name": self.key}]})
            return Response(
                {"layers": [{"id": LAYER_ID, "name": "Recintos"}], "maxRecordCount": PAGE_SIZE}
            )
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
    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.time.sleep", lambda _s: None)

    with pytest.raises(RuntimeError, match=r"Could not read ids \(0 ... 2\]"):
        _read(RESTConverter(), tmp_path)
    assert os.listdir(tmp_path) == []


def test_broken_download_is_not_kept_as_a_page(service, tmp_path, monkeypatch):
    def broken(_source_fs, url, file):
        file.write(b'{"type":"FeatureColl')
        raise ConnectionError("connection reset")

    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.stream_file", broken)
    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.time.sleep", lambda _s: None)

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
            raise ConnectionError("connection reset")
        return real(source_fs, url, file)

    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.stream_file", flaky)
    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.time.sleep", lambda _s: None)

    pages = _read(RESTConverter(), tmp_path)

    assert [len(data) for data, *_ in pages] == [2, 2, 1]
    assert len(attempts) == 4  # three pages, the first of them twice


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
    monkeypatch.setattr("fiboa_cli.conversion.converter_rest.time.sleep", lambda _s: None)

    assert RESTConverter()._rest_id_bound("url", "OBJECTID", None, "ASC") == 7
    assert answers == []


def test_download_files_passes_the_rest_url_through(tmp_path):
    converter = RESTConverter()
    assert converter.download_files({"REST": BASE_URL}, str(tmp_path)) == [BASE_URL]
    assert converter.cache_folder == str(tmp_path)
