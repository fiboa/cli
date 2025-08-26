import numpy as np
from vecorel_cli.conversion.base import BaseConverter

AREA_KEY = "metrics:area"


class FiboaBaseConverter(BaseConverter):
    area_is_in_ha = True
    area_calculate_missing = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extensions.add("https://fiboa.org/specification/v0.3.0/schema.yaml")

    def post_migrate(self, gdf):
        gdf = super().post_migrate(gdf)
        if self.area_calculate_missing:
            # If CRS is not in meters, reproject to an equal-area projection for area calculation
            crs_is_in_meters = gdf.crs.axis_info[0].unit_name in ("m", "metre", "meter")

            # Calculate geometry area; Use original geometries if crs_is_in_meters, else reproject to m-based projection
            base = gdf if crs_is_in_meters else gdf["geometry"].to_crs("EPSG:6933")

            if AREA_KEY in gdf.columns:
                factor = 10_0000 if self.area_is_in_ha else 1
                gdf[AREA_KEY] = np.where(gdf[AREA_KEY] == 0, base.area * factor, gdf[AREA_KEY])
            else:
                gdf[AREA_KEY] = base.area
        elif self.area_is_in_ha and AREA_KEY in gdf.columns:
            # convert area in ha to meters
            gdf[AREA_KEY] *= 10_0000

        return gdf
