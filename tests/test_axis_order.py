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
    # a UTM northing starts at 0, so it contains the whole easting range and
    # both readings fit: leave the coordinates where they are
    ("utm 33n, both readings fit", "EPSG:32633", (300000, 5000000, 500000, 5200000), False),
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


def test_an_empty_frame_is_left_alone():
    gdf = gpd.GeoDataFrame({"geometry": []}, crs="EPSG:3006")
    assert FiboaBaseConverter._traditional_axis_order(gdf) is gdf
