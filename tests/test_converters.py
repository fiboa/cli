from urllib.parse import parse_qs, urlparse

import geopandas as gpd
import pandas as pd
import pytest
import spdx_license_list
from shapely.geometry import Point
from vecorel_cli.vecorel.schemas import VecorelSchema
from vecorel_cli.vecorel.util import load_file

from fiboa_cli.conversion.fiboa_converter import FiboaBaseConverter
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


def test_every_converter_maps_an_id():
    """
    Nothing downstream enforces `id`: columns without a mapping are dropped, so a
    converter that never names one writes a valid file without the identifier
    every collection needs. de_bb and sk were published that way.
    """
    c = Converters()
    for _id in Converters().list_ids():
        c.load(_id)._require_id_mapping()


def test_no_converter_declares_both_sources_and_variants():
    """
    `sources` wins over `variants` in the base converter, so a converter with
    both converts the same file whatever --variant asks for — silently.
    """
    c = Converters()
    for _id in Converters().list_ids():
        c.load(_id)._require_one_source_of_urls()


def test_unique_id_check_ignores_missing_ids():
    """
    A row without an id is dropped downstream under a bounded rule, so it is not
    a repeat: counting nulls as repeats rejected es_cl's C_REFREC, which
    identifies every one of the 13,022,051 recintos that carries it.
    """

    class Converter(FiboaBaseConverter):
        id = "test_unique_ids"
        columns = {"geometry": "geometry", "REF": "id"}

    converter = Converter()
    converter._require_unique_ids(pd.DataFrame({"REF": ["a", "b", None, None]}))

    with pytest.raises(ValueError, match="2 of 3 rows repeat an id"):
        converter._require_unique_ids(pd.DataFrame({"REF": ["a", "a", "a", None]}))


def test_unique_id_check_needs_the_column_in_the_source():
    """
    The mapping existing is not enough: si's 2019 campaign names the field
    POLJINA_ID where every later one names it ID, and the unlisted-column drop
    then wrote 820,151 fields with no id at all — which validated.
    """

    class Converter(FiboaBaseConverter):
        id = "test_missing_id_column"
        columns = {"geometry": "geometry", "ID": "id"}

    with pytest.raises(ValueError, match="none of the columns mapped to 'id'"):
        Converter()._require_unique_ids(pd.DataFrame({"POLJINA_ID": ["a", "b"]}))
