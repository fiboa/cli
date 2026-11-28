"""Values the generic convert test does not check: dates parsed from mixed formats, the
mapping date and area GloCAB keeps for each field, and Trazo's regions and the overlapping
annotations it drops."""

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
    # testsoy's fixture holds its first three rows and 1342 with 1346, a field drawn inside it
    assert by_region.size().to_dict() == {"acre": 3, "chiquitania": 2, "lowmonte": 3, "testsoy": 5}
    years = by_region["determination:datetime"].first().map(lambda d: d.year).to_dict()
    assert years == {"acre": 2020, "chiquitania": 2020, "lowmonte": 2023, "testsoy": 2020}
    assert "split" not in df.columns
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


def test_wri_trazo_annotates_land_once(tmp_parquet_file):
    import geopandas as gpd
    import shapely

    # real fields, renumbered: each file holds the rows named below in the source's order
    df = convert(
        tmp_parquet_file,
        "wri_trazo",
        "wri_trazo",
        # 532 with 534 drawn inside it, 1331 with 1333 in its hole, 1592 = 1537 + 1569 + 1591
        "altoparanaAnnotations_2020.gpkg",
        # rows 0-2, and 1346, a curved field inside 1342 that runs along half of its outline
        "testsoyAnnotations_2020.gpkg",
        # 1922 and its redraw 2336 (94.9% inside it), 1946 with 2350, a copy of it clipped by a
        # chip box, 2016 and 2017, and 2362, 97% covered by 1958 and 2089
        "testmatogrossoAnnotations_2020.gpkg",
        # 439 (inside lowconfidences-479), 1064 (mostly under testmatogrosso-2016/2017), 1413
        "matogrosso_brazil_confidencesAnnotations_2020.gpkg",
        # 245 and 246 under confidences-1413, and 479, a large field mostly annotated nowhere else
        "matogrosso_brazil_lowconfidencesAnnotations_2020.gpkg",
        # the same field drawn twice: 632 and 1388 alike, 876 inside 4550 (which is 89% inside
        # 876), 2444 and 3329 shifted
        "matogrosso_brazil_lcdiAnnotations_2020.gpkg",
        # 1422, subdivided into 596-599 for 86% of its area
        "matogrosso_brazil_lcdibAnnotations_2020.gpkg",
        # 1358 = 197 + 1752 but for thin strips, and 2059, a square inside 2061 along part of
        # its outline, not cut along the chip axes
        "peruvianamazonAnnotations_2022.gpkg",
    )
    assert sorted(df.index) == [
        # the parent outline 1592 makes way for its subdivisions; nested fields and holes stay
        "altoparana-0",
        "altoparana-1",
        "altoparana-2",
        "altoparana-3",
        "altoparana-4",
        "altoparana-5",
        "altoparana-6",
        # the test region is kept, confidences over lowconfidences where half of a field is under
        # the other region's fields
        "matogrosso_brazil_confidences-0",
        "matogrosso_brazil_confidences-2",
        # of two drawings, the one inside the other goes, otherwise the later one
        "matogrosso_brazil_lcdi-0",
        "matogrosso_brazil_lcdi-3",
        "matogrosso_brazil_lcdi-5",
        # a parent its subdivisions don't cover is trimmed to the land they leave
        "matogrosso_brazil_lcdib-0",
        "matogrosso_brazil_lcdib-1",
        "matogrosso_brazil_lcdib-2",
        "matogrosso_brazil_lcdib-3",
        "matogrosso_brazil_lcdib-4",
        "matogrosso_brazil_lowconfidences-2",
        # nothing but thin strips is left of 1358; a field inside another is a clipped copy
        # only where it is cut along the chip axes
        "peruvianamazon-0",
        "peruvianamazon-2",
        "peruvianamazon-3",
        "peruvianamazon-4",
        # the original stays, its redraw and the clipped copy go; 2362 is trimmed
        "testmatogrosso-0",
        "testmatogrosso-1",
        "testmatogrosso-2",
        "testmatogrosso-3",
        "testmatogrosso-4",
        "testmatogrosso-5",
        "testmatogrosso-8",
        # a curved field inside another is not a clipped copy
        "testsoy-0",
        "testsoy-1",
        "testsoy-2",
        "testsoy-3",
        "testsoy-4",
    ]
    holed = shapely.from_wkb(df.loc["altoparana-2", "geometry"])
    assert sum(len(part.interiors) for part in shapely.get_parts(holed)) == 1
    # the trimmed parents keep the land their subdivisions leave, without the strips narrower
    # than 30 m between them: 1.6 of 27 ha and 0.25 of 15 ha
    lcdib = df[df.index.str.startswith("matogrosso_brazil_lcdib")]
    assert lcdib.loc["matogrosso_brazil_lcdib-4", "metrics:area"] == pytest.approx(16_300, rel=0.05)
    assert df.loc["testmatogrosso-8", "metrics:area"] == pytest.approx(2_500, rel=0.05)
    # and stay valid when reprojected
    trimmed = gpd.GeoSeries(
        shapely.from_wkb(df.loc[["matogrosso_brazil_lcdib-4", "testmatogrosso-8"], "geometry"]),
        crs="EPSG:4326",
    )
    for crs in ("EPSG:4326", "EPSG:6933", "EPSG:32721"):
        assert trimmed.to_crs(crs).is_valid.all(), crs
    parent = shapely.from_wkb(lcdib.loc["matogrosso_brazil_lcdib-4", "geometry"])
    pieces = [f"matogrosso_brazil_lcdib-{i}" for i in range(4)]
    pieces = shapely.union_all(shapely.from_wkb(lcdib.loc[pieces, "geometry"]))
    assert shapely.area(shapely.intersection(parent, pieces)) < 0.01 * shapely.area(parent)


def test_wri_trazo_touching_ignores_holes():
    import shapely

    from fiboa_cli.datasets.wri_trazo import TOUCHING, _touches

    # a 1 km square with a hole, and a field inside it along the hole's edge
    outer = shapely.box(0, 0, 1000, 1000).difference(shapely.box(400, 400, 600, 600))
    inner = shapely.box(300, 400, 400, 600)
    assert not _touches(inner, outer, TOUCHING)
    # along the outer edge, it does
    assert _touches(shapely.box(0, 400, 100, 600), outer, TOUCHING)


def test_wri_trazo_clipped_copies_follow_the_chip_axes():
    import pyproj
    import shapely
    from shapely import affinity

    from fiboa_cli.conversion.fiboa_converter import EQUAL_AREA_CRS
    from fiboa_cli.datasets.wri_trazo import _is_clipped

    # a 1 km field near Cuiabá in the equal-area CRS, and a corner of it
    x, y = pyproj.Transformer.from_crs("EPSG:4326", EQUAL_AREA_CRS, always_xy=True).transform(
        -56, -15
    )
    field = shapely.box(x, y, x + 1000, y + 1000)
    corner = shapely.box(x, y, x + 300, y + 300)
    assert _is_clipped(corner, field, "acre")
    # turned by 30°, the cut no longer follows the chip axes
    turned = affinity.rotate(shapely.GeometryCollection([field, corner]), 30, origin=(x, y))
    assert not _is_clipped(turned.geoms[1], turned.geoms[0], "acre")
    # unless it is too short to tell (under 20 m)
    tiny = affinity.rotate(shapely.box(x, y, x + 8, y + 8), 30, origin=(x, y))
    assert _is_clipped(tiny, turned.geoms[0], "acre")


def test_wri_trazo_ml_splits_by_region(tmp_parquet_file):
    df = convert(
        tmp_parquet_file,
        "wri_trazo_ml",
        "wri_trazo",
        "acreAnnotations_2020.gpkg",
        "chiquitaniaAnnotations_2020.gpkg",
        "lowmonteAnnotations_2023.gpkg",
        "testsoyAnnotations_2020.gpkg",
    )
    assert df.groupby("region")["split"].unique().map(list).to_dict() == {
        "acre": ["train"],
        "chiquitania": ["train"],
        "lowmonte": ["train"],
        "testsoy": ["test"],
    }
