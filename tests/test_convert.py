import re
import sys
from csv import DictReader
from unittest.mock import patch

import pyarrow.parquet as pq
from loguru import logger
from pytest import mark

from fiboa_cli.convert import ConvertData
from fiboa_cli.validate import ValidateData

"""
Create input files with: `ogr2ogr output.gpkg -limit 100 input.gpkg`
Optionally use `-lco ENCODING=UTF-8` if you have character encoding issues.
"""

tests = [
    "at",
    "at_block",
    "be_vlg",
    "br_ba_lem",
    "bg",
    "de_sh",
    "de_bb",
    "ec_lv",
    "ec_si",
    "fi",
    "fr",
    "hr",
    "nl",
    "nl_block",
    "pt",
    "dk",
    "be_wal",
    "se",
    "ai4sf",
    "ch",
    "cz",
    "us_usda_cropland",
    "us_ca_scm",
    "jp",
    "lv",
    "ie",
    "es_cat",
    "es",
    "nz",
    "lt",
    "si",
    "sk",
    "jecam",
    "ec_ro",
    "india_10k",
    "it_1",
    "es_ar",
    "es_an",
    "es_cm",
    "es_cl",
]
test_path = "tests/data-files/convert"


def _input_files(converter, *names):
    return {"input_files": {f"{test_path}/{converter}/{name}": name for name in names}}


extra_convert_parameters = {
    "ai4sf": _input_files("ai4sf", "1_vietnam_areas.gpkg", "4_cambodia_areas.gpkg"),
    "nl": {"variant": "2023"},
    "se": {"variant": "2023"},
    "si": {"variant": "2023"},
    "be_vlg": {"variant": "2023"},
    "br_ba_lem": _input_files("br_ba_lem", "LEM_dataset.zip"),
    "ch": _input_files("ch", "lwb_nutzungsflaechen_v2_0_lv95.gpkg"),
    "es_ar": {"variant": "2026", **_input_files("es_ar", "es_ar_44216.shp.zip")},
    "es_cm": {"variant": "2024", **_input_files("es_cm", "es_cm_0.gpkg")},
    "es_cl": {
        "variant": "2025",
        "input_files": {f"{test_path}/es_cl/AVILA.zip": ["replaceme.zip"]},
    },
    "es_an": {
        "variant": "2025",
        "input_files": {f"{test_path}/es_an/SP25_REC_PROV_04.zip": ["SP25_REC_04.shp"]},
    },
    "es_cat": _input_files("es_cat", "Cultius_DUN2023_GPKG.zip"),
    "es": {"input_files": {f"{test_path}/es/1501_ALAVA_cd_2025_20250105.gpkg.zip": ["*.gpkg"]}},
    "lv": _input_files("lv", "1_100.xml"),
    "nz": _input_files("nz", "irrigated-land-area-raw-2020-update.zip"),
    "jecam": _input_files("jecam", "BD_JECAM_CIRAD_2023_feb.shp"),
}


@mark.parametrize("converter", tests)
@patch("fiboa_cli.datasets.commons.hcat.load_ec_mapping")
@patch("fiboa_cli.datasets.commons.ec.load_ec_mapping")
def test_converter(load_ec_mock, load_hcat_mock, capsys, tmp_parquet_file, converter):
    from fiboa_cli import Registry  # noqa

    def load_ec(csv_file=None, url=None):
        original = (csv_file, url)
        if csv_file and "://" in csv_file:
            csv_file = csv_file.split("/")[-1]
        path = url if url and "://" not in url else f"{test_path}/{converter}/{csv_file}"
        try:
            return list(DictReader(open(path, "r", encoding="utf-8")))
        except FileNotFoundError:
            # no local fixture for this mapping: fetch the real one (old behavior)
            from io import StringIO

            from vecorel_cli.vecorel.util import load_file

            from fiboa_cli.datasets.commons.hcat import ec_url

            real = original[1] or ec_url(original[0])
            return list(DictReader(StringIO(load_file(real).decode("utf-8"))))

    load_ec_mock.side_effect = load_ec
    load_hcat_mock.side_effect = load_ec
    logger.remove()
    logger.add(sys.stdout, format="{message}", level="DEBUG", colorize=False)

    path = f"tests/data-files/convert/{converter}"
    kwargs = extra_convert_parameters.get(converter, {})

    ConvertData(converter).convert(target=tmp_parquet_file, cache=path, **kwargs)
    out, err = capsys.readouterr()
    output = out + err

    error = re.search("Skipped - |No schema defined", output)
    if error:
        raise AssertionError(f"Found error in output: '{error.group(0)}'\n\n{output}")

    ValidateData().validate(tmp_parquet_file)

    df = pq.read_table(tmp_parquet_file).to_pandas()
    if "metrics:area" in df.columns and converter not in ("de_bb",):
        # Check for accidental hectare conversion; fields should be more than 10 square meters
        assert (df["metrics:area"] > 10).all()
