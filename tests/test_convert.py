import json
import re
import sys
from contextlib import ExitStack
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

# PT editions besides the default one, 2023
PT_EDITIONS = ("2025", "2022", "2021", "2020", "2019", "2018", "2017")
PT_COLUMNS = (
    "determination:datetime",
    "metrics:area",
    "metrics:perimeter",
    "crop:code",
    "block_id",
    "id",
)

tests = [
    "at",
    "at_block",
    "be_vlg",
    "br_ba_lem",
    "bg",
    "bg#2022",
    "de_sh",
    "de_bb",
    "ec_lt",
    "ec_fr",
    "ec_lv",
    "ec_si",
    "fi",
    "fr",
    "fr#2020",
    "hr",
    "nl",
    "nl_block",
    "pt",
    *(f"pt#{year}" for year in PT_EDITIONS),
    "dk",
    "dk#2008",
    "be_wal",
    "se",
    "ee",
    "ai4sf",
    "ch",
    "cz",
    "cz#2019",
    "cz#2020",
    "us_usda_cropland",
    "us_ca_scm",
    "jp",
    "lv",
    "ie",
    "ie_lpis",
    "ie_lpis#2025",
    "pl",
    "pl_block",
    "es_cat",
    "es_nc",
    "es_ib",
    "es_ib#2024",
    "es_cl",
    "es_ar",
    "es_an",
    "es_cm",
    "es",
    "nz",
    "lt",
    "si",
    "sk",
    "jecam",
    "ec_ro",
    "india_10k",
    "it_1",
    "de_bw",
    "lt_kzs",
    "de_by_block",
    "de_sl_block",
    "de_sl",
    "de_he",
    "de_he#2023",
    "de_st",
    "it_bz",
    "de_sax",
    "de_fusion_ml",
    "za_fusion_ml",
    "rw_rwanda_ml",
]
test_path = "tests/data-files/convert"


def _input_files(converter, *names):
    return {"input_files": {f"{test_path}/{converter}/{name}": name for name in names}}


extra_convert_parameters = {
    "es_nc": {"variant": "2025", **_input_files("es_nc", "es_nc.gpkg")},
    "ai4sf": _input_files("ai4sf", "1_vietnam_areas.gpkg", "4_cambodia_areas.gpkg"),
    "nl": {"variant": "2023"},
    "dk#2008": {"variant": "2008"},
    "pt": {"variant": "2023"},
    **{f"pt#{year}": {"variant": year} for year in PT_EDITIONS},
    # the fixture archive holds the 2024 edition only; the published one holds both
    "lt": {"variant": "2024"},
    # the fixture is the 2023 file; the converter's default is the newest edition
    "fi": {"variant": "2023"},
    "se": {"variant": "2023"},
    "si": {"variant": "2023"},
    "be_vlg": {"variant": "2023"},
    "de_he": _input_files("de_he", "de_he.json"),
    # the older layers publish no land cover class and no declared area
    "de_he#2023": {"variant": "2023", **_input_files("de_he", "de_he_2023.json")},
    "br_ba_lem": _input_files("br_ba_lem", "LEM_dataset.zip"),
    "ch": _input_files("ch", "lwb_nutzungsflaechen_v2_0_lv95.gpkg"),
    "es_cl": {
        "variant": "2025",
        "input_files": {f"{test_path}/es_cl/AVILA.zip": ["replaceme.zip"]},
    },
    "es_ar": {"variant": "2026", **_input_files("es_ar", "es_ar_44216.shp.zip")},
    "ee": {"variant": "2024", **_input_files("ee", "ee_gsaa_2024.gml")},
    "cz#2019": {"variant": "2019"},
    "cz#2020": {"variant": "2020"},
    "es_cm": {"variant": "2024", **_input_files("es_cm", "es_cm_0.gpkg")},
    "es_an": {
        "variant": "2025",
        "input_files": {f"{test_path}/es_an/SP25_REC_PROV_04.zip": ["SP25_REC_04.shp"]},
    },
    "sk#2018": {"variant": "2018"},
    "bg": {"variant": "2025", **_input_files("bg", "bg_agricultural_land_2025.zip")},
    "bg#2022": {"variant": "2022", **_input_files("bg", "bg_agricultural_land_2022.zip")},
    "es_cat": _input_files("es_cat", "Cultius_DUN2023_GPKG.zip"),
    # the fixture is the 2022 archive; the converter's default is the newest edition
    "fr": {"variant": "2022"},
    # two real volumes (.7z.001 + .7z.002), so the parts must be joined before extracting
    "fr#2020": {"variant": "2020"},
    # a page of each service: the current snapshot and a historic year, whose
    # Catxe reads "Febrer2024.0" where the current one reads "maig 2026"
    "es_ib": {"variant": "2026", **_input_files("es_ib", "es_ib_2026.geojson")},
    "es_ib#2024": {"variant": "2024", **_input_files("es_ib", "es_ib_2024.geojson")},
    "es": {"input_files": {f"{test_path}/es/1501_ALAVA_cd_2025_20250105.gpkg.zip": ["*.gpkg"]}},
    "lv": {"variant": "2024", **_input_files("lv", "lv_2024_lielriga.gpkg")},
    # the list on fiboa.org gains the LPIS-only names with this converter, so read the fixture copy
    "ie_lpis": {
        "variant": "2019",
        "mapping_file": f"{test_path}/ie_lpis/ie.csv",
        **_input_files("ie_lpis", "parcels_2019.zip"),
    },
    # the 2025 edition is a GeoPackage with other field names and rows without any attribute
    "ie_lpis#2025": {
        "variant": "2025",
        "mapping_file": f"{test_path}/ie_lpis/ie.csv",
        **_input_files("ie_lpis", "parcels_2025.gpkg"),
    },
    # the code list is minted for this dataset, so read it from the fixture folder
    "pl": {
        "variant": "2026",
        "mapping_file": f"{test_path}/pl/pl.csv",
        **_input_files("pl", "pl_2026_00000000.zip"),
    },
    "pl_block": _input_files("pl_block", "mko_woj_16_akt_public.zip"),
    "nz": _input_files("nz", "irrigated-land-area-raw-2020-update.zip"),
    "jecam": _input_files("jecam", "BD_JECAM_CIRAD_2023_feb.shp"),
    "de_bw": _input_files("de_bw", "de_bw.json"),
    "lt_kzs": _input_files("lt_kzs", "lt_kzs.json"),
    "de_by_block": _input_files("de_by_block", "de_by_block.gml"),
    "de_st": _input_files("de_st", "de_st.json"),
    "de_sl_block": _input_files("de_sl_block", "de_sl_block.gml"),
    "de_sl": _input_files("de_sl", "de_sl.gml"),
    "it_bz": _input_files("it_bz", "it_bz.json"),
    "de_sax": {"input_files": {f"{test_path}/de_sax/gesamt_2026_RE.zip": ["2026_RE_FB_33.shp"]}},
    "de_fusion_ml": _input_files("de_fusion", "de_test_2019.geojson", "de_train_2018.geojson"),
    "za_fusion_ml": _input_files(
        "za_fusion", "za_train_258N.geojson", "za_train_259N.geojson", "za_test_2017.geojson"
    ),
    "rw_rwanda_ml": _input_files("rw_rwanda", "rw_rwanda_2021.geojson"),
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
    # the determination date comes from the year variant
    "dk": ("determination:datetime",),
    "es_nc": ("determination:datetime",),
    "es_cl": ("determination:datetime",),
    "fr": ("determination:datetime",),
    "pl": ("determination:datetime",),
    "ie_lpis": ("determination:datetime", "metrics:area", "crop:code", "id"),
    "ie_lpis#2025": ("determination:datetime", "metrics:area", "crop:code", "id"),
    # derived from the archive date in file_migration()
    "pl_block": ("determination:datetime",),
    # only 2017-2019 and 2023 publish a crop name
    "pt": (*PT_COLUMNS, "crop:name"),
    **{
        f"pt#{year}": (*PT_COLUMNS, "crop:name") if year <= "2019" else PT_COLUMNS
        for year in PT_EDITIONS
    },
}

# Mapping loaders to patch besides commons.ec, e.g. where a converter imports one by name
mapping_lookups = {
    "pt": (
        "fiboa_cli.datasets.commons.hcat.load_ec_mapping",
        "fiboa_cli.datasets.pt.load_ec_mapping",
    ),
}


@mark.parametrize("converter", tests)
@patch("fiboa_cli.datasets.commons.ec.load_ec_mapping")
def test_converter(load_ec_mock, capsys, tmp_parquet_file, converter):
    from fiboa_cli import Registry  # noqa

    # "<id>#<label>" runs a second edition of <id>, from the same folder of input files
    converter_id = converter.split("#")[0]

    def load_ec(csv_file=None, url=None):
        if csv_file and "://" in csv_file:
            csv_file = csv_file.split("/")[-1]
        path = url if url and "://" not in url else f"{test_path}/{converter_id}/{csv_file}"
        return list(DictReader(open(path, "r", encoding="utf-8")))

    load_ec_mock.side_effect = load_ec
    logger.remove()
    logger.add(sys.stdout, format="{message}", level="DEBUG", colorize=False)

    path = f"tests/data-files/convert/{converter_id}"
    kwargs = extra_convert_parameters.get(converter, {})

    with ExitStack() as stack:
        for target in mapping_lookups.get(converter_id, ()):
            stack.enter_context(patch(target, side_effect=load_ec))
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
        constants = (
            json.loads(metadata[b"collection"].decode()) if b"collection" in metadata else {}
        )
        missing = [c for c in required if c not in df.columns and constants.get(c) is None]
        assert not missing, (
            f"{converter} dropped {missing}: absent from the schema and from the "
            f"collection metadata. Produced columns: {sorted(df.columns)}"
        )

    # a float id stringifies as "2315738.0": unique, valid and wrong
    if required and "id" in df.columns:
        floaty = df["id"].astype("string").str.fullmatch(r"-?\d+\.0*").fillna(False)
        assert not floaty.any(), (
            f"{converter}: {int(floaty.sum()):,} id(s) are stringified floats, "
            f"e.g. {df.loc[floaty, 'id'].head(3).tolist()}"
        )

    if "metrics:area" in df.columns and converter not in ("de_bb",):
        # Check for accidental hectare conversion; fields should be more than 10 square meters
        assert (df["metrics:area"] > 10).all()
