"""Europe-LAND's Lithuanian names arrive as Latin-1 mojibake, and two crops carry HCAT2 classes."""

from csv import DictReader
from unittest.mock import patch

import geopandas as gpd
import pyarrow.parquet as pq
from pytest import mark
from shapely.geometry import Point

from fiboa_cli.convert import ConvertData
from fiboa_cli.datasets.commons.encoding import repair_cp1257
from fiboa_cli.datasets.lt import LTConverter

FIXTURES = "tests/data-files/convert/lt"


@mark.parametrize(
    ("value", "expected"),
    [
        ("Þieminiai javai", "Žieminiai javai"),
        ("Ankðtiniai javai", "Ankštiniai javai"),
        ("Ðlapynës", "Šlapynės"),
        ("Kukurûzai", "Kukurūzai"),
        ("Rapsai", "Rapsai"),  # ASCII stays as it is
        ("Žieminiai javai", "Žieminiai javai"),  # already correct: not Latin-1, unchanged
        (None, None),
    ],
)
def test_repair_cp1257(value, expected):
    assert repair_cp1257(value) == expected


def fixture_table(csv_file=None, url=None):
    return list(DictReader(open(f"{FIXTURES}/{csv_file.split('/')[-1]}", encoding="utf-8")))


@patch("fiboa_cli.datasets.commons.hcat.load_hcat_mapping", side_effect=fixture_table)
def test_supplement_corrects_pulses_and_wetlands(_):
    converter = LTConverter()
    converter.select_variant("2025")
    names = ["Ankðtiniai javai", "Ðlapynës", "Þieminiai javai"]
    gdf = gpd.GeoDataFrame(
        {
            "crop_code": names,
            "crop_name": names,
            "EC_trans_n": ["Early cereals", "Spinach", "Winter cereals"],
            "EC_hcat_n": ["spring_unspecified_cereals", "spinach", "winter_unspecified_cereals"],
            "EC_hcat_c": [3301011502, 3301310800, 3301011501],
        },
        geometry=[Point(0, 0)] * 3,
    )
    out = converter.correct_resolved_hcat(converter.migrate(gdf))
    assert out["crop_name"].tolist() == ["Ankštiniai javai", "Šlapynės", "Žieminiai javai"]
    assert out["EC_hcat_c"].astype(str).tolist() == ["3301020000", "3399000000", "3301011501"]
    assert out["EC_hcat_n"].tolist()[:2] == [
        "legumes_dried_pulses_protein_crops",
        "not_known_and_other",
    ]
    assert out["EC_trans_n"].tolist() == ["Leguminous crops", "Wetlands", "Winter cereals"]


@patch("fiboa_cli.datasets.commons.hcat.load_hcat_mapping", side_effect=fixture_table)
def test_converted_names_are_spelled_correctly(_, tmp_parquet_file):
    ConvertData("lt").convert(target=tmp_parquet_file, cache=FIXTURES, variant="2024")
    df = pq.read_table(tmp_parquet_file).to_pandas()
    names = set(df["crop:name"])
    assert {"Žieminiai javai", "Šlapynės", "Kukurūzai"} <= names
    assert not any(c in name for name in names for c in "ðþÐÞûë")
    assert (df["crop:code"] == df["crop:name"]).all()
    wetland = df[df["crop:name"] == "Šlapynės"]
    assert set(wetland["hcat:code"].astype(str)) == {"3399000000"}
