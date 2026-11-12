"""RVO reused crop codes: an edition before the reuse gets the code with an `o` suffix."""

import geopandas as gpd
import pandas as pd
from pytest import mark
from shapely.geometry import Point

from fiboa_cli.datasets.nl import NLCropConverter


def migrate(year: int, codes: list, column: str = "GWS_GEWASCODE") -> list[str]:
    converter = NLCropConverter()
    converter.variant = str(year)
    frame = {column: codes, "geometry": [Point(0, 0)] * len(codes)}
    if column == "GWS_GEWASCODE":
        frame |= {"GWS_GEWAS": ["x"] * len(codes), "CAT_GEWASCATEGORIE": ["Bouwland"] * len(codes)}
    else:
        frame |= {"jaar": [year] * len(codes)}
    gdf = converter.migrate(gpd.GeoDataFrame(frame))
    return list(gdf["gewascode"])


@mark.parametrize(
    ("code", "year", "expected"),
    [
        (1934, 2010, "1934o"),  # starch potatoes, shallots from 2019
        (1934, 2018, "1934o"),
        (1934, 2019, "1934"),
        (1926, 2015, "1926o"),  # seed potatoes, agricultural nature mix from 2016
        (1926, 2016, "1926"),
        (1927, 2016, "1927o"),
        (1927, 2017, "1927"),
        (2951, 2012, "2951"),  # never reused
    ],
)
def test_reused_code_gets_suffix_before_its_new_meaning(code: int, year: int, expected: str):
    assert migrate(year, [code]) == [expected]


def test_newer_editions_keep_their_string_codes():
    assert migrate(2023, ["1934", "259"], column="gewascode") == ["1934", "259"]


def test_codes_are_strings_whatever_the_source_dtype():
    assert migrate(2010, pd.array([259, 1935], dtype="int32")) == ["259", "1935o"]
