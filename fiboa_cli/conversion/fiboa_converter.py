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
        cols = {v: k for k, v in self.columns.items()}
        used_area_key = next((k for k in (AREA_KEY, "area") if k in cols), None)
        if self.area_is_in_ha and used_area_key is not None:
            # convert area in ha to meters
            gdf_key = cols[used_area_key]
            gdf[gdf_key] *= 10_0000

            # let the "rename" functionality rename the legacy key "area" to "metrics:area"
            if used_area_key == "area":
                self.columns[gdf_key] = AREA_KEY

        if self.area_calculate_missing:
            # If CRS is not in meters, reproject to an equal-area projection for area calculation
            crs_is_in_meters = gdf.crs.axis_info[0].unit_name in ("m", "metre", "meter")

            # Calculate geometry area; Use original geometries if crs_is_in_meters, else reproject to m-based projection
            base = gdf if crs_is_in_meters else gdf["geometry"].to_crs("EPSG:6933")

            if AREA_KEY in cols:
                gdf[gdf_key] = np.where(gdf[gdf_key] == 0, base.area, gdf[gdf_key])
            else:
                gdf[AREA_KEY] = base.area

        return gdf
