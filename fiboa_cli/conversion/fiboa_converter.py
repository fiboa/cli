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
        self._require_id_mapping()
        self._require_one_source_of_urls()
        self._prewarm_schemas()
        return super().convert(*args, **kwargs)

    def _require_one_source_of_urls(self):
        """Fail when both `sources` and `variants` are declared.

        The base converter takes `sources` when it is set and ignores the
        variants entirely, so `--variant 2011` silently converts whatever
        `sources` points at. hr declared both and would have published thirteen
        copies of the current file under thirteen different years. A converter
        that inherits variants it does not want says so with `variants = {}`.
        """
        if self.sources and self.variants:
            raise ValueError(
                f"{type(self).__name__} declares both sources and variants; sources wins "
                "and every --variant would convert the same file. Drop sources, or set "
                "variants = {} when the inherited ones do not apply."
            )

    def _require_unique_ids(self, gdf):
        """Fail when the column that becomes `id` does not identify a field.

        fiboa asks for one identifier per field, and the catalog documents `id`
        as unique within an edition, but nothing measured it: es_cl published
        9,109,136 fields whose id was the string "0", us_usda_cropland mapped a
        group id shared by thousands of fields, and every converter that reads
        several files and sets `index_as_id` repeated the same index once per
        file. This runs before geometries are exploded, so it judges what the
        converter assigned rather than the split parts of one source feature.

        A missing id is a different failure, dropped under a bounded rule a few
        lines below, so it is not counted here: es_cl's C_REFREC identifies all
        13,022,051 recintos except the 20 that carry none, and reading those as
        repeats rejected a perfectly good identifier.
        """
        sources = [
            k
            for k, v in self.columns.items()
            if "id" in (v if isinstance(v, (list, tuple)) else [v])
        ]
        column = next(
            (c for c in sources if c in gdf.columns), "id" if "id" in gdf.columns else None
        )
        if column is None:
            # The mapping exists (convert() checks that) but the data does not
            # carry it, and the unlisted-column drop then writes a file without
            # `id` that validates: si published its 2019 edition that way,
            # because that campaign names the field POLJINA_ID and every later
            # one names it ID.
            raise ValueError(
                f"{type(self).__name__}: none of the columns mapped to 'id' "
                f"({', '.join(sources) or 'none'}) is in this source; it has "
                f"{', '.join(sorted(gdf.columns)[:12])}"
            )
        ids = gdf[column].dropna()
        if ids.is_unique:
            return
        counts = ids.value_counts()
        duplicated = int(len(ids) - len(counts))
        worst = int(counts.iloc[0])
        raise ValueError(
            f"{type(self).__name__}: '{column}' is not unique — {duplicated:,} of {len(ids):,} "
            f"rows repeat an id (one appears {worst:,} times), so it cannot be `id`. Map a column "
            "that identifies a field, build one from the source's key columns, or use the row "
            "index (index_as_id) only when the conversion reads a single file."
        )

    def _require_id_mapping(self):
        """Fail before converting when nothing will end up as `id`.

        Every collection needs the identifier, and nothing downstream enforces
        it: the base converter drops columns no mapping names, so a converter
        without one simply writes a file without `id` and validates. That is
        how de_bb and sk reached the catalog without it, and sk shows the
        subtler half — `index_as_id = True` fills the column and the same drop
        step removes it again, because `columns` never named it. A converter
        with no natural key sets both `index_as_id` and `"id": "id"`.
        """
        targets = set()
        for value in list(self.columns.values()) + list(self.column_additions or {}):
            targets.update(value if isinstance(value, (list, tuple)) else [value])
        if "id" not in targets:
            hint = (
                ' — `index_as_id = True` is set, so add \'"id": "id"\' to columns'
                if getattr(self, "index_as_id", False)
                else " — map a unique source column to it, or set index_as_id = True"
                ' and add \'"id": "id"\' to columns'
            )
            raise ValueError(f"{type(self).__name__} maps no column to 'id'{hint}")

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
        attempts = 8
        for uri in sorted(uris):
            for attempt in range(attempts):
                try:
                    load_file(uri)
                    break
                except Exception as e:
                    if attempt == attempts - 1:
                        raise RuntimeError(
                            f"Cannot load schema {uri} after {attempts} attempts: {e}"
                        ) from e
                    self.warning(f"Schema fetch failed ({uri}), retrying: {str(e)[:100]}")
                    # ~4 min of tolerance: vecorel.org outages have outlasted a 30 s budget
                    time.sleep(min(2**attempt * 2, 60))

    def post_migrate(self, gdf):
        gdf = super().post_migrate(gdf)
        self._require_unique_ids(gdf)

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

        # A null or empty geometry cannot be validated, tiled or Hilbert-sorted
        # (geopandas refuses hilbert_distance on such a GeoSeries, which fails the
        # run at the very last step), so drop those rows under the same bounded
        # rule as the required properties.
        if gdf.active_geometry_name is not None:
            geom = gdf.geometry
            blank = geom.isna() | geom.is_empty
            if blank.any():
                share = blank.mean()
                if share > self.max_dropped_share:
                    raise ValueError(
                        f"{int(blank.sum())} of {len(gdf)} rows ({share:.1%}) have an empty or "
                        f"missing geometry; fix the converter instead of dropping them"
                    )
                self.warning(f"Dropping {int(blank.sum())} rows with an empty or missing geometry")
                gdf = gdf[~blank]

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
