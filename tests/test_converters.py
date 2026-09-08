import pandas as pd
import pytest
import spdx_license_list
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
    converter = Converters().load("es_cl")
    converter._require_unique_ids(pd.DataFrame({"C_REFREC": ["a", "b", None, None]}))

    with pytest.raises(ValueError, match="2 of 3 rows repeat an id"):
        converter._require_unique_ids(pd.DataFrame({"C_REFREC": ["a", "a", "a", None]}))
