import json
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
    "pt#2025",
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
    "de_by_block",
    "de_he",
]
test_path = "tests/data-files/convert"


def _input_files(converter, *names):
    return {"input_files": {f"{test_path}/{converter}/{name}": name for name in names}}


extra_convert_parameters = {
    "ai4sf": _input_files("ai4sf", "1_vietnam_areas.gpkg", "4_cambodia_areas.gpkg"),
    "nl": {"variant": "2023"},
    "pt": {"variant": "2023"},
    "pt#2025": {"variant": "2025"},
    "se": {"variant": "2023"},
    "si": {"variant": "2023"},
    "be_vlg": {"variant": "2023"},
    "de_he": _input_files("de_he", "de_he.json"),
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
    "fr": {"variant": "2022"},
    "es": {"input_files": {f"{test_path}/es/1501_ALAVA_cd_2025_20250105.gpkg.zip": ["*.gpkg"]}},
    "lv": _input_files("lv", "1_100.xml"),
    "nz": _input_files("nz", "irrigated-land-area-raw-2020-update.zip"),
    "jecam": _input_files("jecam", "BD_JECAM_CIRAD_2023_feb.shp"),
    "de_by_block": _input_files("de_by_block", "de_by_block.gml"),
}


# Columns a converter must actually deliver.
#
# An optional column goes missing silently: the source spelling drifts between
# editions, the mapping stops matching, the base converter warns once ("Column
# 'X' not found in dataset, removing from schema") and validation still passes
# because the field is optional. That is exactly how de_sh published a 2026
# edition carrying neither determination:datetime nor metrics:area.
#
# A value that is constant across the whole edition is written once into the
# collection metadata rather than as a column, so both places count as
# delivered -- de_sh's 2026 fixture is a single campaign date.
#
# Keyed like extra_convert_parameters, so "<id>#<label>" can state a different
# expectation per edition where the editions genuinely differ.
expected_columns = {
    "de_sh": ("determination:datetime", "metrics:area", "flik", "hbn", "id"),
}


@mark.parametrize("converter", tests)
@patch("fiboa_cli.datasets.commons.hcat.load_ec_mapping")
@patch("fiboa_cli.datasets.commons.ec.load_ec_mapping")
def test_converter(load_ec_mock, load_hcat_mock, capsys, tmp_parquet_file, converter):
    from fiboa_cli import Registry  # noqa

    # "<id>#<label>" runs a second edition of <id>, from the same folder of input files
    converter_id = converter.split("#")[0]

    def load_ec(csv_file=None, url=None):
        original = (csv_file, url)
        if csv_file and "://" in csv_file:
            csv_file = csv_file.split("/")[-1]
        path = url if url and "://" not in url else f"{test_path}/{converter_id}/{csv_file}"
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

    path = f"{test_path}/{converter_id}"
    kwargs = extra_convert_parameters.get(converter, {})

    ConvertData(converter_id).convert(target=tmp_parquet_file, cache=path, **kwargs)
    out, err = capsys.readouterr()
    output = out + err

    error = re.search("Skipped - |No schema defined", output)
    if error:
        raise AssertionError(f"Found error in output: '{error.group(0)}'\n\n{output}")

    ValidateData().validate(tmp_parquet_file)

    df = pq.read_table(tmp_parquet_file).to_pandas()

    required = expected_columns.get(converter)
    if required:
        metadata = pq.ParquetFile(tmp_parquet_file).schema_arrow.metadata or {}
        constants = json.loads(metadata[b"collection"].decode()) if b"collection" in metadata else {}
        missing = [c for c in required if c not in df.columns and constants.get(c) is None]
        assert not missing, (
            f"{converter} dropped {missing}: absent from the schema and from the "
            f"collection metadata. Produced columns: {sorted(df.columns)}"
        )

    if "metrics:area" in df.columns and converter_id not in ("de_bb",):
        # Check for accidental hectare conversion; fields should be more than 10 square meters
        assert (df["metrics:area"] > 10).all()
