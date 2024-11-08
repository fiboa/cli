import re
import tempfile
from pytest import fixture, mark
from fiboa_cli import convert, validate
from click.testing import CliRunner

"""
Create input files with: `ogr2ogr output.gpkg -limit 100 input.gpkg`
"""

@fixture
def out_file():
    with tempfile.NamedTemporaryFile() as out:
        yield out

tests = ['at', 'be_vlg', 'br_ba_lem', 'de_sh', 'ec_lv', 'ec_si', 'fi', 'fr', 'hr', 'nl', 'nl_crop', 'pt', 'dk', 'be_wa', 'se', 'ai4sf']
extra_convert_parameters = {
    "se": ["-m", f"tests/data-files/convert/se/se_2021.csv"],
    "ai4sf": ['-i', 'tests/data-files/convert/ai4sf/1_vietnam_areas.gpkg', '-i', 'tests/data-files/convert/ai4sf/4_cambodia_areas.gpkg'],
}


@mark.parametrize('converter', tests)
def test_converter(out_file, converter):
    path = f"tests/data-files/convert/{converter}"
    runner = CliRunner()
    args = [converter, '-o', out_file.name, '-c', path] + extra_convert_parameters.get(converter, [])
    result = runner.invoke(convert, args)
    assert result.exit_code == 0, result.output
    error = re.search('Skipped - |No schema defined', result.output)
    if error:
        raise AssertionError(f"Found error in output: '{error.group(0)}'\n\n{result.output}")

    result = runner.invoke(validate, [out_file.name, '--data'])
    assert result.exit_code == 0, result.output
