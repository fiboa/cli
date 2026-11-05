"""crop:name carries the source's own crop names; where a table supplies them, they must be
intact and attached to the right code."""

import geopandas as gpd
import pandas as pd
from shapely.geometry import box

from fiboa_cli.datasets.commons.hcat import repair_names
from fiboa_cli.datasets.de_mv import Converter as DEMV
from fiboa_cli.datasets.hr import Converter as HR


def test_repair_takes_the_other_tables_name_only_where_it_matches():
    names = {"001": "p?enica (jara)", "405": "me?ana raba (polj??ine)", "002": "rž"}
    rows = [
        {"original_code": "001", "original_name": "pšenica (jara)"},
        # worded differently: not this code's name in the damaged edition
        {"original_code": "405", "original_name": "mešana raba pod 0,1 ha (poljščine)"},
        {"original_code": "002", "original_name": "rž (jara)"},
    ]
    repaired = repair_names(names, rows)
    assert repaired["001"] == "pšenica (jara)"
    assert repaired["405"] == "me?ana raba (polj??ine)"
    # an intact name is never replaced
    assert repaired["002"] == "rž"


def test_corrections_win_over_the_table():
    converter = HR()
    converter.hcat_mapping = [
        {"original_code": "200", "original_name": "Staklenici na oranici"},
        {"original_code": "210", "original_name": "Staklenici na oranici"},
    ]
    gdf = gpd.GeoDataFrame({"land_use_id": ["200", "210"]}, geometry=[box(0, 0, 1, 1)] * 2)
    names = converter.add_crop_names(gdf)["crop:name"].tolist()
    assert names == ["Oranica", "Staklenici na oranici"]


def test_de_mv_names_match_the_code_whatever_its_case():
    gdf = gpd.GeoDataFrame({"bodennutzu": ["AF", "WA", "Wa", None]}, geometry=[box(0, 0, 1, 1)] * 4)
    out = DEMV().migrate(gdf)
    assert out["crop:name"].tolist()[:3] == ["Ackerfläche", "Wald", "Wald"]
    assert out["crop:name_en"].tolist()[:3] == ["Arable land", "Forest", "Forest"]
    assert pd.isna(out["crop:name"].iloc[3])
