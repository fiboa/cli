"""crop:name carries the source's own crop names; where a table supplies them, they must be
intact and attached to the right code."""

import geopandas as gpd
import pandas as pd
from shapely.geometry import box

from fiboa_cli.datasets.de_mv import Converter as DEMV
from fiboa_cli.datasets.ec_es import Converter as ECES
from fiboa_cli.datasets.hr import Converter as HR

HR_TABLE = [
    {
        "original_code": "200",
        "original_name": "Staklenici na oranici",
        "translated_name": "Arable land",
        "HCAT3_name": "arable_crops",
        "HCAT3_code": "3301000000",
    },
    {
        "original_code": "210",
        "original_name": "Staklenici na oranici",
        "translated_name": "Greenhouses on arable land",
        "HCAT3_name": "arable_crops",
        "HCAT3_code": "3301000000",
    },
]


def _gdf(column, values):
    return gpd.GeoDataFrame({column: values}, geometry=[box(0, 0, 1, 1)] * len(values))


def test_post_migrate_names_the_codes_after_hcat():
    converter = type("HRNames", (HR,), {"crop_names_from_table": True})()
    converter.hcat_mapping = HR_TABLE
    out = converter.post_migrate(_gdf("land_use_id", ["200", "210"]))
    assert out["crop:name"].tolist() == ["Staklenici na oranici", "Staklenici na oranici"]
    assert out["hcat:name_en"].tolist() == ["Arable land", "Greenhouses on arable land"]


def test_a_converter_without_the_opt_in_gets_no_names_from_its_table():
    # hr_2020.csv names the codes of every edition from 2011, which reuse some of them
    assert not HR().crop_names_from_table
    # es.csv is made for the 2025 campaign; EuroCrops' 2021-2023 files may use its codes otherwise
    converter = ECES()
    assert not converter.crop_names_from_table
    assert "crop:name" not in converter.columns.values()
    converter.hcat_mapping = [{**HR_TABLE[0], "original_code": "1", "original_name": "TRIGO"}]
    out = converter.post_migrate(_gdf("original_code", ["1"]))
    assert out["hcat:code"].tolist() == ["3301000000"]
    assert "crop:name" not in out.columns


def test_de_mv_names_match_the_code_whatever_its_case():
    gdf = _gdf("bodennutzu", ["AF", "WA", "Wa", None])
    out = DEMV().post_migrate(gdf)
    assert out["crop:name"].tolist()[:3] == ["Ackerfläche", "Wald", "Wald"]
    assert out["crop:name_en"].tolist()[:3] == ["Arable land", "Forest", "Forest"]
    assert pd.isna(out["crop:name"].iloc[3])
    assert set(out["crop:code_list"]) == {"https://fiboa.org/code/de/de_mv.csv"}


def test_de_mv_codes_take_the_code_lists_spelling():
    # the service writes WA, its code list Wa: the published code must be in its own list
    out = DEMV().post_migrate(_gdf("bodennutzu", ["WA", "wa", "AF", "aöd", "XX", None]))
    codes = out["bodennutzu"].tolist()
    assert codes[:5] == ["Wa", "Wa", "AF", "AÖD", "XX"]
    assert pd.isna(codes[5])
