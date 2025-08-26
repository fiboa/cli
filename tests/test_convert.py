import re
import sys
from csv import DictReader
from unittest.mock import patch

from loguru import logger
from pytest import mark
from vecorel_cli.convert import ConvertData
from vecorel_cli.validate import ValidateData

"""
Create input files with: `ogr2ogr output.gpkg -limit 100 input.gpkg`
Optionally use `-lco ENCODING=UTF-8` if you have character encoding issues.
"""

tests = [
    "at",
    "at_crop",
    "be_vlg",
    "br_ba_lem",
    "de_sh",
    # "ec_lv",  needs ec-schema
    # "ec_si",
    "fi",
    # "fr",  needs hcat-schema
    "hr",
    "nl",
    "nl_crop",
    "pt",
    "dk",
    "be_wal",
    "se",
    "ai4sf",
    "ch",
    "cz",
    "us_usda_cropland",
    "jp",
    # "lv", needs hcat-schema
    "ie",
    "es_cat",
    "nz",
    # "lt", needs hcat-schema
    "si",
    "sk",
    "jecam",
    # "ec_ro", needs hcat-schema
    "india_10k",
]
test_path = "tests/data-files/convert"


def _input_files(converter, *names):
    return {"input_files": {f"{test_path}/{converter}/{name}": name for name in names}}


extra_convert_parameters = {
    "ai4sf": _input_files("ai4sf", "1_vietnam_areas.gpkg", "4_cambodia_areas.gpkg"),
    "nl_crop": {"variant": 2023},
    "be_vlg": {"variant": 2023},
    "br_ba_lem": _input_files("br_ba_lem", "LEM_dataset.zip"),
    "ch": _input_files("ch", "lwb_nutzungsflaechen_v2_0_lv95.gpkg"),
    "es_cat": _input_files("es_cat", "Cultius_DUN2023_GPKG.zip"),
    "lv": _input_files("lv", "1_100.xml"),
    "nz": _input_files("nz", "irrigated-land-area-raw-2020-update.zip"),
    "jecam": _input_files("jecam", "BD_JECAM_CIRAD_2023_feb.shp"),
}


@mark.parametrize("converter", tests)
@patch("fiboa_cli.datasets.commons.ec.load_ec_mapping")
def test_converter(load_ec_mock, capsys, tmp_parquet, converter, block_stream_file):
    from fiboa_cli import Registry  # noqa

    def load_ec(csv_file=None, url=None):
        path = url if url and "://" not in url else f"{test_path}/{converter}/{csv_file}"
        return list(DictReader(open(path, "r")))

    load_ec_mock.side_effect = load_ec
    logger.remove()
    logger.add(sys.stdout, format="{message}", level="DEBUG", colorize=False)

    path = f"tests/data-files/convert/{converter}"
    kwargs = extra_convert_parameters.get(converter, {})

    ConvertData(converter).convert(target=tmp_parquet.name, cache=path, **kwargs)
    out, err = capsys.readouterr()
    output = out + err

    error = re.search("Skipped - |No schema defined", output)
    if error:
        raise AssertionError(f"Found error in output: '{error.group(0)}'\n\n{output}")

    ValidateData().validate(tmp_parquet.name)
