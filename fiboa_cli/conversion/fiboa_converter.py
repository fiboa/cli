import numpy as np
from vecorel_cli.conversion.base import BaseConverter

from ..fiboa.version import get_fiboa_uri

AREA_KEY = "metrics:area"
# Properties that a schema requires to be non-null; rows lacking them cannot
# validate, so they are dropped (with a warning) rather than failing the run.
REQUIRED_NON_NULL = ("id", "crop:code")


class FiboaBaseConverter(BaseConverter):
    area_is_in_ha = True
    area_calculate_missing = False
    use_variant_as_determination = False
    # rows lacking a REQUIRED_NON_NULL value are dropped up to this share, else it's an error
    max_dropped_share = 0.01

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extensions.add(get_fiboa_uri())
        if self.use_variant_as_determination:
            # The column is added in post_migrate; list it so it survives the
            # "remove unlisted columns" step of the base converter.
            self.columns = {**self.columns, "determination:datetime": "determination:datetime"}

    def convert(self, *args, **kwargs):
        self._prewarm_schemas()
        return super().convert(*args, **kwargs)

    def _prewarm_schemas(self):
        """Fetch every schema this conversion will need before doing any real
        work, with retries. The schema hosts (vecorel.org, fiboa.org) fail
        intermittently; without this, a transient blip after a long source
        download kills the conversion at the very last step. load_file caches
        per process, so a successful pre-warm makes the write network-free."""
        import time

        from vecorel_cli.vecorel.util import load_file
        from vecorel_cli.vecorel.version import vecorel_version

        uris = set(self.extensions)
        uris.add(get_fiboa_uri())
        uris.add(f"https://vecorel.org/specification/v{vecorel_version}/schema.yaml")
        for uri in sorted(uris):
            for attempt in range(5):
                try:
                    load_file(uri)
                    break
                except Exception as e:
                    if attempt == 4:
                        raise RuntimeError(f"Cannot load schema {uri} after 5 attempts: {e}") from e
                    self.warning(f"Schema fetch failed ({uri}), retrying: {str(e)[:100]}")
                    time.sleep(2**attempt * 2)

    def post_migrate(self, gdf):
        gdf = super().post_migrate(gdf)

        # post_migrate runs before columns are renamed, so look up the source column
        for key in REQUIRED_NON_NULL:
            for src, dst in self.columns.items():
                targets = dst if isinstance(dst, (list, tuple)) else [dst]
                if key in targets and src in gdf.columns:
                    nulls = gdf[src].isna()
                    if nulls.any():
                        share = nulls.mean()
                        if share > self.max_dropped_share:
                            raise ValueError(
                                f"{int(nulls.sum())} of {len(gdf)} rows ({share:.1%}) have no "
                                f"{key} ({src}); fix the converter instead of dropping them"
                            )
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
