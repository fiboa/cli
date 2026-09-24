import pyproj
import shapely
from vecorel_cli.conversion.base import BaseConverter

from ..fiboa.version import get_fiboa_uri

AREA_KEY = "metrics:area"


def _swap_xy(coords):
    """Exchange the first two coordinate columns, leaving any others (z) in place"""
    coords = coords.copy()
    coords[:, [0, 1]] = coords[:, [1, 0]]
    return coords


class FiboaBaseConverter(BaseConverter):
    area_is_in_ha = True
    area_calculate_missing = False
    use_variant_as_determination = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extensions.add(get_fiboa_uri())

    def _source_column(self, target):
        """The source column that `columns` maps to `target`; the rename comes later."""
        for source, mapped in self.columns.items():
            if target == mapped or (isinstance(mapped, (list, tuple)) and target in mapped):
                return source
        return None

    @staticmethod
    def _traditional_axis_order(gdf):
        """Fix swapped x/y coordinates for faulty projections (e.g. SWEREF99 TM)"""
        crs = gdf.crs
        if (
            crs is not None
            and crs.is_projected
            and crs.axis_info
            and crs.axis_info[0].direction.lower() == "north"
            and crs.area_of_use
            and not gdf.empty
        ):
            area = crs.area_of_use
            to_crs = pyproj.Transformer.from_crs("EPSG:4326", crs, always_xy=True)
            east, north = to_crs.transform(
                [area.west, area.east, area.west, area.east],
                [area.south, area.south, area.north, area.north],
            )
            bounds = gdf.total_bounds  # in the order the coordinates are stored
            fits = min(east) <= bounds[0] and bounds[2] <= max(east)
            swapped = min(north) <= bounds[0] and bounds[2] <= max(north)
            if not fits and swapped:
                return gdf.set_geometry(
                    shapely.transform(gdf.geometry.values, _swap_xy, include_z=None)
                )
        return gdf

    @staticmethod
    def _crs_in_meters(gdf):
        return bool(
            gdf.crs
            and gdf.crs.axis_info
            and gdf.crs.axis_info[0].unit_name in ("m", "metre", "meter")
        )

    def post_migrate(self, gdf):
        gdf = super().post_migrate(gdf)
        gdf = self._traditional_axis_order(gdf)

        area_key = self._source_column(AREA_KEY)
        crs_is_in_meters = self._crs_in_meters(gdf)

        def in_metres(geometry):
            # Reprojecting is costly, so only the geometries whose area is computed are,
            # and only when the CRS is not in metres: to an equal-area projection.
            return geometry if crs_is_in_meters else geometry.to_crs("EPSG:6933")

        if self.area_calculate_missing:
            if area_key in gdf.columns:
                factor = 10_000 if self.area_is_in_ha else 1
                missing = (gdf[area_key] == 0).to_numpy()
                if missing.any():
                    gdf.loc[missing, area_key] = in_metres(gdf.geometry[missing]).area * factor
            else:
                gdf[area_key] = in_metres(gdf.geometry).area
        elif self.area_is_in_ha and area_key in gdf.columns:
            # convert area in ha to meters
            gdf[area_key] = gdf[area_key].astype(float) * 10_000

        if self.use_variant_as_determination:
            gdf["determination:datetime"] = f"{self.variant}-01-01T00:00:00Z"
        return gdf
