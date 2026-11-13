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


# 2005-2008: shapefiles with truncated column names, and for 2007-2008 a
# projection file without an EPSG code
ROUNDED_RD = (
    "+proj=sterea +lat_0=52.156161 +lon_0=5.387639 +k=0.999908 "
    "+x_0=155000 +y_0=463000 +ellps=bessel +units=m"
)


def shapefile(year: int, rows: list[tuple]) -> gpd.GeoDataFrame:
    converter = NLCropConverter()
    converter.variant = str(year)
    frame = gpd.GeoDataFrame(
        {
            "ID_GEOMETR": range(len(rows)),
            "CAT_GEWASC": [r[0] for r in rows],
            "GWS_GEWAS": [r[1] for r in rows],
            "GWS_GEWASC": [r[2] for r in rows],
            "geometry": [Point(155000, 463000)] * len(rows),
        },
        crs=ROUNDED_RD,
    )
    return converter.filter_rows(converter.migrate(frame))


def test_shapefile_columns_and_year():
    gdf = shapefile(2005, [("Bouwland", "Overige toegestane voedergewassen", "657")])
    assert gdf[["category", "gewas", "gewascode", "jaar"]].values.tolist() == [
        ["Bouwland", "Overige toegestane voedergewassen", "657o", 2005]
    ]


def test_shapefile_crs_is_rd_new():
    assert shapefile(2008, [("Grasland", "Grasland, blijvend", "265")]).crs.to_epsg() == 28992


def test_old_editions_keep_fallow_and_uncategorised_crops():
    rows = [
        ("Bouwland", "Maïs, snij-", "259"),
        ("Grasland", "Grasland, blijvend", "265"),
        ("Braakland", "Braak, groene- 5 meter", "1804"),
        (None, "Graszaad, Engels raai 1e jaar", "2030"),
        ("Natuurterrein", "Overige natuurterreinen", "866"),
        ("Overige", "Bos (SBL-regeling)", "2027"),
    ]
    assert list(shapefile(2008, rows)["gewascode"]) == ["259", "265", "1804", "2030"]
