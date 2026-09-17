"""The x coordinate of a GeoParquet geometry is always the easting, whatever
axis order the source CRS declares."""

import geopandas as gpd
import pytest
import shapely

from fiboa_cli.conversion.fiboa_converter import FiboaBaseConverter

# label, CRS, the bounds as stored, whether they must be swapped
cases = [
    # SWEREF99 TM declares AXIS["Northing", NORTH] first; Sweden's archives
    # store the coordinates that way, and 6.1M does not fit an easting
    ("sweden as declared", "EPSG:3006", (6132000, 269097, 7670000, 915128), True),
    ("sweden already fixed", "EPSG:3006", (269097, 6132000, 915128, 7670000), False),
    # declares the easting first, so there is nothing to judge
    ("utm 33n", "EPSG:32633", (300000, 5000000, 500000, 5200000), False),
    # Poland CS92 declares the northing first too, but its northings (137k to
    # 908k) and eastings (145k to 877k) overlap, so both readings fit: leave the
    # coordinates where they are
    ("poland cs92, both readings fit", "EPSG:2180", (500000, 600000, 510000, 610000), False),
    # not projected, so there is nothing to judge
    ("etrs89 degrees", "EPSG:4258", (-6, 39, -5, 40), False),
]


@pytest.mark.parametrize("label,crs,bounds,expected", [(c[0], c[1], c[2], c[3]) for c in cases])
def test_traditional_axis_order(label, crs, bounds, expected):
    xmin, ymin, xmax, ymax = bounds
    gdf = gpd.GeoDataFrame({"geometry": [shapely.box(xmin, ymin, xmax, ymax)]}, crs=crs)

    result = FiboaBaseConverter._traditional_axis_order(gdf).total_bounds

    if expected:
        assert (round(result[0]), round(result[1])) == (ymin, xmin), "should have been swapped"
    else:
        assert (round(result[0]), round(result[1])) == (xmin, ymin), "should have been left alone"


def test_the_swap_keeps_z():
    """--original-geometries must deliver the source's z coordinates, so the
    swap may not flatten them"""
    gdf = gpd.GeoDataFrame(
        {
            "geometry": [
                shapely.Polygon([(6132000, 269097, 5), (6132000, 300000, 6), (6200000, 300000, 7)]),
                shapely.Polygon([(6132000, 269097), (6132000, 300000), (6200000, 300000)]),
            ]
        },
        crs="EPSG:3006",
    )

    result = FiboaBaseConverter._traditional_axis_order(gdf).geometry

    assert list(result.array.has_z) == [True, False]
    assert list(result.iloc[0].exterior.coords)[:2] == [(269097, 6132000, 5), (300000, 6132000, 6)]
    assert list(result.iloc[1].exterior.coords)[:2] == [(269097, 6132000), (300000, 6132000)]


def test_an_empty_frame_is_left_alone():
    gdf = gpd.GeoDataFrame({"geometry": []}, crs="EPSG:3006")
    assert FiboaBaseConverter._traditional_axis_order(gdf) is gdf
