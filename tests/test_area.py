"""metrics:area is measured from the geometry where the source has none (fiboa/cli#277),
in m², whatever CRS the source is in."""

import math

import geopandas as gpd
import pytest
from pyproj import Geod
from shapely.geometry import Point, Polygon, box

from fiboa_cli.conversion.fiboa_converter import FiboaBaseConverter

# two fields of about 1.6 ha near 10°E, 50°N, in lon/lat
FIELDS = [box(10.0, 50.0, 10.002, 50.001), box(10.01, 50.0, 10.012, 50.001)]
GEODESIC = [abs(Geod(ellps="WGS84").geometry_area_perimeter(f)[0]) for f in FIELDS]


def _convert(tmp_parquet_file, crs="EPSG:4326", data=None, geometries=None, **attrs):
    columns = {"geometry": "geometry", "id": "id", **attrs.pop("columns", {})}
    converter = type(
        "Converter",
        (FiboaBaseConverter,),
        {
            "id": "area",
            "short_name": "Area",
            "title": "Area",
            "description": "Area",
            "license": "CC0-1.0",
            "columns": columns,
            **attrs,
        },
    )()
    if geometries is not None:  # given in `crs`
        gdf = gpd.GeoDataFrame({"id": ["a", "b"], **(data or {})}, geometry=geometries, crs=crs)
    else:
        gdf = gpd.GeoDataFrame({"id": ["a", "b"], **(data or {})}, geometry=FIELDS, crs=4326)
        gdf = gdf.to_crs(crs) if crs else gdf.set_crs(None, allow_override=True)
    src = tmp_parquet_file.parent / "source.parquet"
    gdf.to_parquet(src)
    converter.convert(tmp_parquet_file, input_files={str(src): "source.parquet"})
    return gpd.read_parquet(tmp_parquet_file).sort_values("id")


@pytest.mark.parametrize(
    "crs,rel",
    [
        ("EPSG:4326", 1e-6),  # degrees: reprojected
        ("EPSG:3857", 1e-6),  # metres, but 2.4 times the area at 50°N: reprojected
        ("EPSG:3035", 1e-6),  # LAEA Europe, equal-area: measured in place
        ("EPSG:25832", 1e-3),  # UTM 32N, 1° off its central meridian: measured in place
    ],
)
def test_the_area_is_measured_where_the_source_has_none(tmp_parquet_file, crs, rel):
    result = _convert(tmp_parquet_file, crs)

    assert result["metrics:area"].tolist() == pytest.approx(GEODESIC, rel=rel)


@pytest.mark.parametrize(
    "crs,expected",
    [
        ("EPSG:4326", False),  # degrees
        ("EPSG:3857", False),  # metres, not equal-area
        ("EPSG:2263", False),  # US survey feet
        ("EPSG:3035", True),
        ("EPSG:25832", True),
    ],
)
def test_which_crs_measures_area_in_place(crs, expected):
    geometry = gpd.GeoSeries(FIELDS, crs="EPSG:4326").to_crs(crs)

    assert FiboaBaseConverter._crs_measures_area(geometry) is expected


def test_hectares_are_converted_and_the_gaps_filled(tmp_parquet_file):
    result = _convert(
        tmp_parquet_file,
        "EPSG:25832",
        data={"flaeche": [1.5, math.nan]},
        columns={"flaeche": "metrics:area"},
    )

    assert result["metrics:area"].iloc[0] == 15_000
    assert result["metrics:area"].iloc[1] == pytest.approx(GEODESIC[1], rel=1e-3)


def test_a_zero_area_in_square_metres_is_measured(tmp_parquet_file):
    result = _convert(
        tmp_parquet_file,
        "EPSG:25832",
        data={"shape_area": [0.0, 1234.5]},
        columns={"shape_area": "metrics:area"},
        area_is_in_ha=False,
    )

    assert result["metrics:area"].iloc[0] == pytest.approx(GEODESIC[0], rel=1e-3)
    assert result["metrics:area"].iloc[1] == 1234.5


def test_the_measured_area_is_not_taken_for_hectares(tmp_parquet_file):
    # area_is_in_ha describes a mapped source column, not the area measured in m²
    result = _convert(tmp_parquet_file, "EPSG:25832", area_is_in_ha=True)

    assert result["metrics:area"].tolist() == pytest.approx(GEODESIC, rel=1e-3)


@pytest.mark.parametrize("crs", ["EPSG:25832", "EPSG:3857"])  # measured in place, reprojected
def test_the_area_of_an_invalid_geometry_is_that_of_the_published_one(tmp_parquet_file, crs):
    x, y = gpd.GeoSeries([Point(9.5, 50.0)], crs=4326).to_crs(crs).iloc[0].coords[0]
    # a figure-8, whose planar area is 0 before make_valid() splits it into two triangles
    figure_8 = Polygon([(x, y), (x + 100, y + 100), (x + 100, y), (x, y + 100)])
    field = box(x + 200, y, x + 300, y + 100)

    result = _convert(tmp_parquet_file, crs, geometries=[figure_8, field])

    published = result.geometry.to_crs("EPSG:6933").area
    assert result["metrics:area"].iloc[0] > 0
    assert result["metrics:area"].tolist() == pytest.approx(published.tolist(), rel=5e-3)


def test_opting_out_publishes_no_area(tmp_parquet_file):
    result = _convert(tmp_parquet_file, area_calculate_missing=False)

    assert "metrics:area" not in result.columns


def test_without_a_crs_the_area_is_left_out(tmp_parquet_file):
    result = _convert(tmp_parquet_file, crs=None)

    assert "metrics:area" not in result.columns
