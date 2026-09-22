import pyproj
import shapely
from vecorel_cli.conversion.base import BaseConverter

from ..fiboa.version import get_fiboa_uri

AREA_KEY = "metrics:area"
PERIMETER_KEY = "metrics:perimeter"
DETERMINATION_KEY = "determination:datetime"
# marks the rows that split_multipart() made out of one source feature
SPLIT_KEY = "__split_part"


def _swap_xy(coords):
    """Exchange the first two coordinate columns, leaving any others (z) in place"""
    coords = coords.copy()
    coords[:, [0, 1]] = coords[:, [1, 0]]
    return coords


class FiboaBaseConverter(BaseConverter):
    area_is_in_ha = True
    area_calculate_missing = False
    # None (the default) resolves per edition: a converter whose variants are years
    # and that maps no determination:datetime of its own takes the variant year as
    # the determination date. Set True/False to force it on or off. See #284.
    use_variant_as_determination = None

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

    def _variants_are_years(self):
        """Whether every declared variant is a year in the range 1900–2100."""
        return bool(self.variants) and all(
            str(v).isdigit() and 1900 <= int(v) <= 2100 for v in self.variants
        )

    def _determination_provided(self, gdf):
        """Whether the converter already supplies determination:datetime — mapped from a
        source column, added as a constant, or present on the frame — so the variant year
        must not overwrite it. The column renames come after post_migrate(), so a mapped
        determination still lives under its source name here."""
        return (
            DETERMINATION_KEY in gdf.columns
            or self._source_column(DETERMINATION_KEY) is not None
            or DETERMINATION_KEY in (self.column_additions or {})
        )

    def _use_variant_as_determination(self, gdf):
        """Resolve use_variant_as_determination for this edition. An explicit True/False
        wins; the default (None) fills the determination date from the variant only when
        the variants are years and the converter provides no determination itself (#284)."""
        if self.use_variant_as_determination is not None:
            return self.use_variant_as_determination
        return self._variants_are_years() and not self._determination_provided(gdf)

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

    def post_migrate(self, gdf):
        gdf = super().post_migrate(gdf)
        gdf = self._traditional_axis_order(gdf)

        area_key = self._source_column(AREA_KEY)
        crs_is_in_meters = bool(
            gdf.crs
            and gdf.crs.axis_info
            and gdf.crs.axis_info[0].unit_name in ("m", "metre", "meter")
        )

        def in_metres(geometry):
            # Reprojecting is costly, so only the geometries whose area is computed are,
            # and only when the CRS is not in metres: to an equal-area projection.
            return geometry if crs_is_in_meters else geometry.to_crs("EPSG:6933")

        if SPLIT_KEY in gdf.columns:
            split = gdf.pop(SPLIT_KEY).fillna(False).astype(bool).to_numpy()
            if split.any():
                # the parts of one source feature inherited its area and perimeter
                parts = gdf.geometry[split]
                if area_key in gdf.columns:
                    factor = (
                        10_000 if self.area_is_in_ha and not self.area_calculate_missing else 1
                    )
                    gdf.loc[split, area_key] = in_metres(parts).area / factor
                perimeter_key = self._source_column(PERIMETER_KEY)
                if perimeter_key in gdf.columns:
                    # an equal-area projection distorts lengths, so measure those in UTM
                    lengths = parts if crs_is_in_meters else parts.to_crs(parts.estimate_utm_crs())
                    gdf.loc[split, perimeter_key] = lengths.length

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

        if self._use_variant_as_determination(gdf):
            gdf[DETERMINATION_KEY] = f"{self.variant}-01-01T00:00:00Z"
        return gdf
