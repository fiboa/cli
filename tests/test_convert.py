import re
from pytest import fixture, mark
from fiboa_cli import convert, validate
from click.testing import CliRunner

"""
Create input files with: `ogr2ogr output.gpkg -limit 100 input.gpkg`
"""

tests = ['at', 'be_vlg', 'br_ba_lem', 'de_sh', 'ec_lv', 'ec_si', 'fi', 'fr', 'hr', 'nl', 'nl_crop', 'pt', 'dk', 'be_wal', 'se', 'ai4sf', 'ch', 'cz', 'us_usda_cropland', 'jp', 'lv', 'ie', 'nz']
test_path = "tests/data-files/convert"
extra_convert_parameters = {
    "nl_crop": ["--year=2023"],
    "br_ba_lem": ["-i", f"{test_path}/br_ba_lem/LEM_dataset.zip"],
    "fr": ["-m", f"{test_path}/fr/fr_2018.csv"],
    "lv": ["-i", f"{test_path}/lv/1_100.xml", "-m", f"{test_path}/lv/lv_2021.csv"],
    "se": ["-m", f"{test_path}/se/se_2021.csv"],
    "ch": ["-i", f"{test_path}/ch/lwb_nutzungsflaechen_v2_0_lv95.gpkg"],
    "ai4sf": ['-i', f'{test_path}/ai4sf/1_vietnam_areas.gpkg', '-i', f'{test_path}/ai4sf/4_cambodia_areas.gpkg'],
    "nz": ["-i", f"{test_path}/nz/irrigated-land-area-raw-2020-update.zip"],
}


@mark.parametrize('converter', tests)
def test_converter(tmp_file, converter, block_stream_file):
    path = f"tests/data-files/convert/{converter}"
    runner = CliRunner()
    args = [converter, '-o', tmp_file.name, '-c', path] + extra_convert_parameters.get(converter, [])
    result = runner.invoke(convert, args)
    assert result.exit_code == 0, result.output
    error = re.search('Skipped - |No schema defined', result.output)
    if error:
        raise AssertionError(f"Found error in output: '{error.group(0)}'\n\n{result.output}")

    result = runner.invoke(validate, [tmp_file.name, '--data'])
    assert result.exit_code == 0, result.output
