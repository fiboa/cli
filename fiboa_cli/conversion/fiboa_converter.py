import numpy as np
import pyproj
import shapely
from vecorel_cli.conversion.base import BaseConverter

from ..fiboa.version import get_fiboa_uri

AREA_KEY = "metrics:area"


class FiboaBaseConverter(BaseConverter):
    area_is_in_ha = True
    area_calculate_missing = False
    use_variant_as_determination = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extensions.add(get_fiboa_uri())

    @staticmethod
    def _traditional_axis_order(gdf):
        """Put the easting in x, whatever the source's CRS says.

        EPSG defines SWEREF99 TM and a few others northing first, and a source
        that honours that ships its coordinates that way: Jordbruksverket's
        shapefile declares AXIS["Northing", NORTH] before AXIS["Easting", EAST]
        and writes them so. GeoParquet stores x, y, so everything after this
        point — the tiles, the STAC bbox, the bbox covering column — reads such
        a file as (lat, lon), and Sweden lands in the Indian Ocean.

        The declaration alone is not enough to act on: most sources in a
        lat-lon-ordered CRS (EPSG:4258, 4326) still store lon, lat. So the
        coordinates have to disagree with the CRS's own area of use as well.
        """
        crs = gdf.crs
        if crs is None or not crs.is_projected or not crs.axis_info:
            return gdf
        if crs.axis_info[0].direction.lower() != "north":
            return gdf
        area = crs.area_of_use
        if area is None or gdf.empty:
            return gdf
        to_crs = pyproj.Transformer.from_crs("EPSG:4326", crs, always_xy=True)
        east, north = to_crs.transform(
            [area.west, area.east, area.west, area.east],
            [area.south, area.south, area.north, area.north],
        )
        bounds = gdf.total_bounds  # in the order the coordinates are stored
        fits = min(east) <= bounds[0] and bounds[2] <= max(east)
        swapped = min(north) <= bounds[0] and bounds[2] <= max(north)
        if fits or not swapped:
            return gdf
        return gdf.set_geometry(
            shapely.transform(gdf.geometry.values, lambda coords: coords[:, ::-1])
        )

    def post_migrate(self, gdf):
        gdf = super().post_migrate(gdf)
        gdf = self._traditional_axis_order(gdf)

        gdf_area_key = next((k for k, v in self.columns.items() if v == AREA_KEY), None)
        if self.area_calculate_missing:
            # If CRS is not in meters, reproject to an equal-area projection for area calculation
            crs_is_in_meters = gdf.crs.axis_info[0].unit_name in ("m", "metre", "meter")

            # Calculate geometry area; Use original geometries if crs_is_in_meters, else reproject to m-based projection
            base = gdf if crs_is_in_meters else gdf["geometry"].to_crs("EPSG:6933")

            if gdf_area_key in gdf.columns:
                factor = 10_000 if self.area_is_in_ha else 1
                gdf[gdf_area_key] = np.where(
                    gdf[gdf_area_key] == 0, base.area * factor, gdf[gdf_area_key]
                )
            else:
                gdf[gdf_area_key] = base.area
        elif self.area_is_in_ha and gdf_area_key in gdf.columns:
            # convert area in ha to meters
            gdf[gdf_area_key] = gdf[gdf_area_key].astype(float) * 10_000

        if self.use_variant_as_determination:
            gdf["determination:datetime"] = f"{self.variant}-01-01T00:00:00Z"
        return gdf
