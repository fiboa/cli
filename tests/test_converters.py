from click.testing import CliRunner

from fiboa_cli import converters
from fiboa_cli.datasets.commons.euro_land import EuroLandBaseConverter
from fiboa_cli.datasets.lt import LTConverter


def test_describe():
    runner = CliRunner()
    result = runner.invoke(converters, [])
    assert result.exit_code == 0, result.output
    assert "Short Title" in result.output
    assert "License" in result.output
    assert "be_vlg" in result.output
    assert "Belgium, Flanders" in result.output
    assert "None" not in result.output


class MyConverter(EuroLandBaseConverter):
    id = "test"
    short_name = title = description = "Test"
    crop_code_list = "test"


def test_mutability():
    converter_1 = LTConverter()
    assert len(converter_1.providers) == 2

    converter_2 = LTConverter()
    assert len(converter_2.providers) == 2


def test_mutability2():
    converter_1 = LTConverter()

    m = MyConverter()
    assert m.column_additions["crop:code_list"] == "test"
    assert converter_1.column_additions["crop:code_list"] != "test"

    assert len(converter_1.providers) == 2
    assert len(m.providers) == 1

    m.extensions.add("test")
    assert "test" not in converter_1.extensions
