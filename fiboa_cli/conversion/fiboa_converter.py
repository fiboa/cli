import re

import pyproj
import shapely
from vecorel_cli.conversion.base import BaseConverter

from ..fiboa.version import get_fiboa_uri

AREA_KEY = "metrics:area"
DETERMINATION_KEY = "determination:datetime"
# Equal-area (WGS 84 / NSIDC EASE-Grid 2.0 Global): the area of a geometry reprojected
# to it matches the geodesic area to ~1e-9, at any latitude. Equal Earth (EPSG:8857)
# would serve as well.
EQUAL_AREA_CRS = "EPSG:6933"
# The largest areal distortion of the source CRS across the data that is still measured
# in place: UTM/TM grids stay within it (EPSG:25832 is 0.28% off at 15°E), Web Mercator
# does not (+140% at 50°N).
AREA_DISTORTION_TOLERANCE = 0.005


def _swap_xy(coords):
    """Exchange the first two coordinate columns, leaving any others (z) in place"""
    coords = coords.copy()
    coords[:, [0, 1]] = coords[:, [1, 0]]
    return coords


class FiboaBaseConverter(BaseConverter):
    # The unit of the source column mapped to metrics:area; fiboa publishes m².
    area_is_in_ha = True
    # Measure metrics:area from the geometry where the source has none: for every row
    # if no column maps to it, otherwise for the rows that are empty or 0. See #277.
    area_calculate_missing = True
    # None (the default) resolves per edition: a converter whose variants are years
    # and that maps no determination:datetime of its own takes the variant year as
    # the determination date. Set True/False to force it on or off. See #284.
    use_variant_as_determination = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extensions.add(get_fiboa_uri())

    def _source_column(self, target, columns=None):
        """The source column that `columns` (default: the declared ones) maps to
        `target`; the rename comes later."""
        for source, mapped in (self.columns if columns is None else columns).items():
            if target == mapped or (isinstance(mapped, (list, tuple)) and target in mapped):
                return source
        return None

    # Also called after the migrations (post_migrate, add_hcat): overrides must be side-effect free
    def get_columns(self, gdf):
        columns = super().get_columns(gdf)
        self._area_added = (
            self._source_column(AREA_KEY, columns) is None and self.area_calculate_missing
        )
        if self._area_added:
            # post_migrate() measures it; the mapping keeps the column in the output
            columns[AREA_KEY] = AREA_KEY
        return columns

    def _variants_are_years(self):
        """Whether every declared variant is a year in the range 1900–2100."""
        # four ASCII digits: isdigit() also accepts e.g. "²" (int() fails) and "02023"
        return bool(self.variants) and all(
            re.fullmatch("[0-9]{4}", str(v)) and 1900 <= int(v) <= 2100 for v in self.variants
        )

    def _determination_provided(self):
        """Whether the converter supplies determination:datetime itself: mapped from a
        source column (a self-mapping means the converter fills the column in its own
        code) or added as a constant."""
        # the declared constants: the instance copy also holds the variant date added below
        return (
            self._source_column(DETERMINATION_KEY) is not None
            or DETERMINATION_KEY in type(self).column_additions
        )

    def _use_variant_as_determination(self):
        """Resolve use_variant_as_determination for this edition. An explicit True/False
        wins; the default (None) fills the determination date from the variant only when
        the variants are years and the converter provides no determination itself (#284)."""
        if self.use_variant_as_determination is not None:
            return self.use_variant_as_determination
        return self._variants_are_years() and not self._determination_provided()

    def select_variant(self, variant):
        super().select_variant(variant)
        # a constant column: the base converter adds it and keeps it in the output
        if self.variant is not None and self._use_variant_as_determination():
            self.column_additions[DETERMINATION_KEY] = f"{self.variant}-01-01T00:00:00Z"

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
    def _crs_measures_area(geometry):
        """Whether the planar area in the CRS of `geometry` is the area in m²: a projected
        CRS in metres whose areal distortion across the data is within the tolerance.
        Anything that cannot be checked counts as not, so that it is reprojected."""
        crs = geometry.crs
        if not (
            crs.is_projected
            and crs.axis_info
            and all(axis.unit_name in ("m", "metre", "meter") for axis in crs.axis_info[:2])
        ):
            return False
        try:
            minx, miny, maxx, maxy = geometry.total_bounds
            # the corners and the centre of the data, as lon/lat of the CRS's own datum
            to_lonlat = pyproj.Transformer.from_crs(crs, crs.geodetic_crs, always_xy=True)
            lon, lat = to_lonlat.transform(
                [minx, maxx, minx, maxx, (minx + maxx) / 2],
                [miny, miny, maxy, maxy, (miny + maxy) / 2],
            )
            scale = pyproj.Proj(crs).get_factors(lon, lat, errcheck=True).areal_scale
            return max(abs(s - 1) for s in scale) <= AREA_DISTORTION_TOLERANCE
        except Exception:
            return False

    def _measure_area(self, geometry):
        """The area of each geometry in m². Reprojecting is costly, so it is done only
        for the geometries passed and only if their CRS does not measure area in place."""
        # The base converter repairs the geometries only after post_migrate(), and the
        # area of an invalid one is wrong (0 for a figure-8), so repair them for the area:
        # make_valid() is what the published geometry gets too.
        invalid = ~geometry.is_valid & geometry.notna()
        if invalid.any():
            geometry = geometry.copy()
            geometry[invalid] = geometry[invalid].make_valid()
        if not self._crs_measures_area(geometry):
            geometry = geometry.to_crs(EQUAL_AREA_CRS)
        return geometry.area

    def post_migrate(self, gdf):
        gdf = super().post_migrate(gdf)
        gdf = self._traditional_axis_order(gdf)

        # the final mapping, with what an override changes after this class's get_columns()
        area_key = self._source_column(AREA_KEY, self.get_columns(gdf))
        in_ha = self.area_is_in_ha and not self._area_added
        if area_key is None:
            return gdf

        if area_key in gdf.columns:
            gdf[area_key] = gdf[area_key].astype(float)
            if in_ha:
                gdf[area_key] *= 10_000
            missing = (gdf[area_key].isna() | (gdf[area_key] <= 0)).to_numpy()
        else:
            missing = None  # no area in this source (edition) at all

        if not self.area_calculate_missing or (missing is not None and not missing.any()):
            return gdf
        if gdf.crs is None:
            self.warning(f"No CRS, so {AREA_KEY} can't be measured from the geometries")
            return gdf

        if missing is None:
            gdf[area_key] = self._measure_area(gdf.geometry)
        else:
            gdf.loc[missing, area_key] = self._measure_area(gdf.geometry[missing])
        return gdf
