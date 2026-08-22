import numpy as np
from vecorel_cli.conversion.base import BaseConverter

from ..fiboa.version import get_fiboa_uri

AREA_KEY = "metrics:area"
# Properties that a schema requires to be non-null; rows lacking them cannot
# validate, so they are dropped (with a warning) rather than failing the run.
REQUIRED_NON_NULL = ("crop:code",)


class FiboaBaseConverter(BaseConverter):
    area_is_in_ha = True
    area_calculate_missing = False
    use_variant_as_determination = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extensions.add(get_fiboa_uri())
        if self.use_variant_as_determination:
            # The column is added in post_migrate; list it so it survives the
            # "remove unlisted columns" step of the base converter.
            self.columns = {**self.columns, "determination:datetime": "determination:datetime"}

    def post_migrate(self, gdf):
        gdf = super().post_migrate(gdf)

        # post_migrate runs before columns are renamed, so look up the source column
        for key in REQUIRED_NON_NULL:
            for src, dst in self.columns.items():
                targets = dst if isinstance(dst, (list, tuple)) else [dst]
                if key in targets and src in gdf.columns:
                    nulls = gdf[src].isna()
                    if nulls.any():
                        self.warning(
                            f"Dropping {int(nulls.sum())} rows without a value for {key} ({src})"
                        )
                        gdf = gdf[~nulls]

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
