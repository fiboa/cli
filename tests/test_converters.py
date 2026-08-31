from urllib.parse import parse_qs, urlparse

import geopandas as gpd
import spdx_license_list
from shapely.geometry import Point
from vecorel_cli.vecorel.schemas import VecorelSchema
from vecorel_cli.vecorel.util import load_file

from fiboa_cli.converters import Converters
from fiboa_cli.fiboa.version import get_fiboa_uri


def test_converters(capsys):
    from fiboa_cli import Registry  # noqa

    Converters().converters()
    out, err = capsys.readouterr()
    output = out + err

    assert "Short Title" in output
    assert "License" in output
    assert "at" in output
    assert "Austria" in output
    # assert "None" not in output


def test_changed_properties():
    c = Converters()
    for _id in Converters().list_ids():
        converter = c.load(_id)
        assert converter.license is None or isinstance(converter.license, str)
        assert converter.provider is None is None or isinstance(converter.provider, str)


def test_valid_license():
    c = Converters()
    for _id in Converters().list_ids():
        converter = c.load(_id)
        if converter.license and "<" not in converter.license:
            assert converter.license.upper() in spdx_license_list.LICENSES, (
                f"Converter {_id} has invalid license {converter.license}"
            )
        assert getattr(converter, "license") is None or isinstance(converter.license, str)
        assert getattr(converter, "provider") is None or isinstance(converter.provider, str)


def test_rest_query_params(monkeypatch, tmp_folder):
    """
    The paging filter must be combined with rest_params["where"] rather than replace it,
    and rest_format must drive both the "f" parameter and the cached page extension.
    """
    # lt_kzs is the converter that sets rest_format="json" and a rest_params["where"]
    converter = Converters().load("lt_kzs")
    converter.cache_folder = str(tmp_folder)

    class Response:
        def json(self):
            # maxRecordCount above the page length below, so paging stops after one page
            return {"layers": [{"id": 0}], "maxRecordCount": 1000}

    monkeypatch.setattr(
        "fiboa_cli.conversion.converter_rest.requests.get", lambda url, params: Response()
    )

    requested, read = [], []
    monkeypatch.setattr(
        "fiboa_cli.conversion.converter_rest.stream_file",
        lambda fs, uri, file: (requested.append(uri), file.write(b"{}")),
    )

    def fake_read_file(path, *args, **kwargs):
        read.append(path)
        return gpd.GeoDataFrame({"OBJECTID": [1]}, geometry=[Point(0, 0)], crs="EPSG:4326")

    monkeypatch.setattr(gpd, "read_file", fake_read_file)

    list(converter.get_data([converter.rest_base_url]))

    assert len(requested) == 1, "Expected exactly one page"
    query = parse_qs(urlparse(requested[0]).query)
    assert query["f"] == ["json"], "rest_format must drive the output format"
    assert query["outSR"] == ["4326"], "rest_params must survive into the query"
    assert query["where"] == ["OBJECTID>-1 AND (GKODAS IN ('bl1','bl1b'))"], (
        "The paging filter must be combined with rest_params['where'], not replace it"
    )
    assert read[0].endswith(".json"), (
        f"rest_format must drive the cached page extension, got {read[0]}"
    )


def test_overriden_base_properties():
    """
    You should not define a different schema for a property if it is defined in the base schema.
    """
    c = Converters()
    for _id in Converters().list_ids():
        converter = c.load(_id)
        schemas = converter.missing_schemas
        converter_properties = schemas and schemas.get("properties") or {}
        schema = VecorelSchema(load_file(get_fiboa_uri()))

        for property, s in schema["properties"].items():
            if property in converter_properties:
                assert s == converter_properties[property], (
                    "Converter {converter} overrides schema for base property {property}"
                )
