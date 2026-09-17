import numpy as np
import shapely
from vecorel_cli.conversion.base import BaseConverter

from ..fiboa.version import get_fiboa_uri

AREA_KEY = "metrics:area"
PERIMETER_KEY = "metrics:perimeter"
# marks the rows that split_multipart() made out of one source feature
SPLIT_KEY = "__split_part"


class FiboaBaseConverter(BaseConverter):
    area_is_in_ha = True
    area_calculate_missing = False
    use_variant_as_determination = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extensions.add(get_fiboa_uri())

    def split_multipart(self, gdf):
        """
        Split multi-part geometries into one row per polygon.

        The base converter does the same, but only after it has checked the ids. A
        converter that mints its ids in file_migration(), migrate() or post_migrate()
        splits first, so that it can number the parts that share an id. The parts keep
        the attributes of the source feature, so post_migrate() recomputes the area and
        perimeter of the rows this made: the source values describe the whole feature.
        """
        gdf.geometry = gdf.geometry.make_valid()
        gdf[SPLIT_KEY] = shapely.get_num_geometries(gdf.geometry.values) > 1
        gdf = gdf.explode(index_parts=False)
        gdf = gdf[(gdf.geometry.geom_type == "Polygon") & gdf.geometry.is_valid]
        # explode repeats the source row labels, which misaligns a later assignment
        return gdf.reset_index(drop=True)

    def _source_column(self, target):
        """The source column that `columns` maps to `target`; the rename comes later."""
        for source, mapped in self.columns.items():
            if target == mapped or (isinstance(mapped, (list, tuple)) and target in mapped):
                return source
        return None

    def post_migrate(self, gdf):
        gdf = super().post_migrate(gdf)

        area_key = self._source_column(AREA_KEY)
        # If CRS is not in meters, reproject to an equal-area projection for area calculation
        crs_is_in_meters = gdf.crs.axis_info[0].unit_name in ("m", "metre", "meter")
        metric = gdf.geometry if crs_is_in_meters else gdf.geometry.to_crs("EPSG:6933")

        if SPLIT_KEY in gdf.columns:
            split = gdf.pop(SPLIT_KEY).fillna(False).astype(bool).to_numpy()
            if split.any():
                # the parts of one source feature inherited its area and perimeter
                if area_key in gdf.columns:
                    factor = 10_000 if self.area_is_in_ha else 1
                    gdf.loc[split, area_key] = metric.area[split] / factor
                perimeter_key = self._source_column(PERIMETER_KEY)
                if perimeter_key in gdf.columns:
                    # an equal-area projection distorts lengths, so measure those in UTM
                    lengths = (
                        gdf.geometry
                        if crs_is_in_meters
                        else gdf.geometry.to_crs(gdf.estimate_utm_crs())
                    )
                    gdf.loc[split, perimeter_key] = lengths.length[split]

        if self.area_calculate_missing:
            if area_key in gdf.columns:
                factor = 10_000 if self.area_is_in_ha else 1
                gdf[area_key] = np.where(gdf[area_key] == 0, metric.area * factor, gdf[area_key])
            else:
                gdf[area_key] = metric.area
        elif self.area_is_in_ha and area_key in gdf.columns:
            # convert area in ha to meters
            gdf[area_key] = gdf[area_key].astype(float) * 10_000

        if self.use_variant_as_determination:
            gdf["determination:datetime"] = f"{self.variant}-01-01T00:00:00Z"
        return gdf
