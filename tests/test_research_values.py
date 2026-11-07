"""Values the generic convert test does not check: dates parsed from mixed formats, the
mapping date and area GloCAB keeps for each field, and Trazo's regions."""

import datetime

import pyarrow.parquet as pq
import pytest
from loguru import logger

from fiboa_cli.convert import ConvertData

FIXTURES = "tests/data-files/convert"


def convert(tmp_parquet_file, converter, folder, *files, **kwargs):
    logger.remove()
    input_files = {f"{FIXTURES}/{folder}/{name}": name for name in files}
    ConvertData(converter).convert(
        target=tmp_parquet_file, cache=f"{FIXTURES}/{folder}", input_files=input_files, **kwargs
    )
    return pq.read_table(tmp_parquet_file).to_pandas().set_index("id")


def test_ecaas_dates_are_month_first(tmp_parquet_file):
    df = convert(
        tmp_parquet_file,
        "ke_ecaas",
        "ke_ecaas",
        "ecaas_geojson_kenya.geojson",
        mapping_file=f"{FIXTURES}/ke_ecaas/crop.csv",
    )
    # the source writes 11/14/2021 and 2/28/2022: month/day/year
    row = df.loc["ad0898f5-caf1-457c-93c8-885615392e83"]
    assert row["planting_date"] == datetime.date(2021, 11, 14)
    assert row["harvest_date"] == datetime.date(2022, 2, 28)
    # ad4bbf18: 12/1/2021 is 1 December, not 12 January
    assert df.loc["ad4bbf18-f796-42f8-9d66-e1fdb56d1b72", "planting_date"] == datetime.date(
        2021, 12, 1
    )
    # ISO dates pass unchanged
    row = df.loc["faf1c636-e855-43f6-adc8-a48ff4e9fea5"]
    assert row["planting_date"] == datetime.date(2021, 7, 29)
    assert row["harvest_date"] == datetime.date(2021, 12, 10)
    # the source's crop name is kept as it is written, next to HCAT
    assert row["crop:name"] == "Irish_Potatoes"
    assert row["hcat:name"] == "potatoes"


def test_glocab_keeps_every_region_with_its_month(tmp_parquet_file):
    df = convert(tmp_parquet_file, "glocab", "glocab", "glocab.gpkg")
    months = (
        df.groupby("region")["determination:datetime"]
        .unique()
        .map(lambda dates: [d.strftime("%Y-%m") for d in dates])
    )
    # one file for all mapping years; each field keeps its region's month, so a year can be subset
    assert months.to_dict() == {
        "Brazil_A": ["2019-08"],
        "Russia_E": ["2018-10"],
        "USA_E": ["2017-09"],
        "Ukraine_A": ["2017-03"],
        "Ukraine_D": ["2016-08"],
    }
    assert set(df["admin:country_code"]) == {"BR", "RU", "UA", "US"}
    # USA_E has 8 ordinary fields and 4 flagged multi-field polygons in the fixture
    assert df.loc[df["region"] == "USA_E", "no_area"].sum() == 4
    # measured from the geometry (the source's Area_km2 is wrong in USA_C), in m²
    assert df.loc["Ukraine_A-0", "metrics:area"] == pytest.approx(364_972, rel=0.01)


def test_wri_trazo_regions(tmp_parquet_file):
    import shapely

    df = convert(
        tmp_parquet_file,
        "wri_trazo",
        "wri_trazo",
        "acreAnnotations_2020.gpkg",
        "chiquitaniaAnnotations_2020.gpkg",
        "lowmonteAnnotations_2023.gpkg",
        "testsoyAnnotations_2020.gpkg",
    )
    by_region = df.groupby("region")
    # chiquitania's file holds its second and third polygon twice: kept once, ids stay row numbers
    assert sorted(df.index[df["region"] == "chiquitania"]) == ["chiquitania-0", "chiquitania-1"]
    assert by_region.size().to_dict() == {"acre": 3, "chiquitania": 2, "lowmonte": 3, "testsoy": 3}
    years = by_region["determination:datetime"].first().map(lambda d: d.year).to_dict()
    assert years == {"acre": 2020, "chiquitania": 2020, "lowmonte": 2023, "testsoy": 2020}
    assert by_region["split"].unique().map(list).to_dict() == {
        "acre": ["train"],
        "chiquitania": ["train"],
        "lowmonte": ["train"],
        "testsoy": ["test"],
    }
    assert by_region["basemap"].first().to_dict()["chiquitania"] == "sentinel-2"
    # UTM 20S (chiquitania) and a file without a CRS (lowmonte) both land in lon/lat
    centroids = {
        region: shapely.from_wkb(geometry).centroid.coords[0]
        for region, geometry in zip(df["region"], df["geometry"])
    }
    lon, lat = centroids["chiquitania"]
    assert -63 < lon < -62 and -17.5 < lat < -16.5
    lon, lat = centroids["lowmonte"]
    assert -66 < lon < -63 and -39.5 < lat < -37.5
