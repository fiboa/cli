import json
import os
from typing import Optional

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from .fiboa_converter import FiboaBaseConverter

GEO_META_KEY = b"geo"
DEFAULT_BATCH_SIZE = 64_000


# This converter is experimental, use with caution.
# Use this primarily for datasets that are too large to be processed by the default converter
class PerFileBaseConverter(FiboaBaseConverter):
    def convert(
        self,
        output_file,
        cache=None,
        input_files=None,
        variant=None,
        compression=None,
        compression_level: Optional[int] = None,
        geoparquet_version=None,
        original_geometries=False,
        **kwargs,
    ) -> str:
        dirname, filename = os.path.split(output_file)
        filename, ext = os.path.splitext(filename)
        if input_files is not None and isinstance(input_files, dict) and len(input_files) > 0:
            self.warning("Using user provided input file(s) instead of the pre-defined file(s)")
            urls = input_files
        else:
            urls = self.get_urls()
            if urls is None:
                raise ValueError("No input files provided")

        # Single-source: the per-file pipeline degenerates to plain convert.
        if len(urls) <= 1:
            return super().convert(
                output_file=output_file,
                cache=cache,
                input_files=urls,
                variant=variant,
                compression=compression,
                compression_level=compression_level,
                geoparquet_version=geoparquet_version,
                original_geometries=original_geometries,
                **kwargs,
            )

        # Multi-source: convert each URI to its own GeoParquet part, then merge.
        part_files = []
        for index, (uri, target) in enumerate(urls.items()):
            part = os.path.join(dirname, f"{filename}_{index}{ext}")
            self.info(f"Converting source {index + 1}/{len(urls)}: {uri}")
            super().convert(
                output_file=part,
                cache=cache,
                input_files={uri: target},
                variant=variant,
                compression=compression,
                compression_level=compression_level,
                geoparquet_version=geoparquet_version,
                original_geometries=original_geometries,
                **kwargs,
            )
            part_files.append(part)
        self.merge_files(output_file, part_files, compression=compression or "zstd")
        return output_file

    def merge_files(
        self,
        output_file: str,
        paths: list,
        batch_size: int = DEFAULT_BATCH_SIZE,
        compression: str = "zstd",
        compression_level: Optional[int] = None,
        cleanup_parts: bool = False,
    ) -> str:
        """
        Merge a list of GeoParquet files into a single GeoParquet, globally
        sorted by Hilbert distance. Streams via pyarrow row groups so peak
        memory is roughly O(batch_size * k).

        Assumes each input file was produced by the standard convert pipeline,
        which already sorts rows by Hilbert distance against the CRS's total
        bounds (see ``vecorel_cli.vecorel.hilbert.hilbert_sort_geodataframe``).
        Because every input shares the same Hilbert reference grid (derived
        from the CRS, not from per-file extents), no pre-sort is required —
        we just merge the already-sorted runs.
        """
        if not paths:
            raise ValueError("No paths to merge")
        paths = [str(p) for p in paths]

        base_pf = pq.ParquetFile(paths[0])
        base_schema = base_pf.schema_arrow
        base_meta = base_schema.metadata or {}
        if GEO_META_KEY not in base_meta:
            raise ValueError(f"{paths[0]} has no 'geo' metadata; not a GeoParquet?")
        base_geo = json.loads(base_meta[GEO_META_KEY])
        primary_col = base_geo["primary_column"]
        primary_col_meta = base_geo["columns"][primary_col]
        crs = primary_col_meta.get("crs")

        # Validate schemas + CRS, collect per-file bboxes / geometry_types for
        # the merged geo metadata.
        bboxes: list = []
        geom_types: set = set()
        if primary_col_meta.get("bbox") is not None:
            bboxes.append(primary_col_meta["bbox"])
        geom_types.update(primary_col_meta.get("geometry_types") or [])
        for path in paths[1:]:
            pf = pq.ParquetFile(path)
            sch = pf.schema_arrow
            if not sch.equals(base_schema, check_metadata=False):
                raise ValueError(
                    f"Schema mismatch: {path} differs from {paths[0]}.\n"
                    f"  Expected: {base_schema}\n"
                    f"  Got:      {sch}"
                )
            geo = json.loads((sch.metadata or {})[GEO_META_KEY])
            col = geo["columns"][primary_col]
            if col.get("crs") != crs:
                raise ValueError(
                    f"CRS mismatch: {path} has crs={col.get('crs')!r}, expected {crs!r}"
                )
            if col.get("bbox") is not None:
                bboxes.append(col["bbox"])
            geom_types.update(col.get("geometry_types") or [])

        merged_bbox = None
        if bboxes:
            merged_bbox = (
                min(b[0] for b in bboxes),
                min(b[1] for b in bboxes),
                max(b[2] for b in bboxes),
                max(b[3] for b in bboxes),
            )

        # Same Hilbert reference grid that the upstream sort used.
        from vecorel_cli.vecorel.hilbert import crs_total_bounds

        total_bounds = crs_total_bounds(crs)

        self.info(f"Streaming merge -> {output_file} (Hilbert ref bounds = {total_bounds})")
        _streaming_merge(
            paths,
            output_file,
            primary_col,
            total_bounds,
            merged_bbox,
            sorted(geom_types),
            batch_size,
            compression,
            compression_level,
        )

        if cleanup_parts:
            for path in paths:
                try:
                    os.remove(path)
                except OSError:
                    self.warning(f"Could not remove part file {path}")

        return output_file


# ---------- helpers ----------


def _bounds_array_for_table(table: pa.Table, primary_col: str) -> np.ndarray:
    """Return an (N, 4) float64 array of [xmin, ymin, xmax, ymax] per feature.

    Uses the GeoParquet 1.1.0 covering ``bbox`` struct column when present
    (zero-decode); otherwise falls back to decoding WKB.
    """
    if "bbox" in table.column_names and pa.types.is_struct(table.column("bbox").type):
        arr = table.column("bbox").combine_chunks()
        return np.column_stack(
            [
                arr.field("xmin").to_numpy(zero_copy_only=False),
                arr.field("ymin").to_numpy(zero_copy_only=False),
                arr.field("xmax").to_numpy(zero_copy_only=False),
                arr.field("ymax").to_numpy(zero_copy_only=False),
            ]
        ).astype(np.float64, copy=False)
    import shapely

    wkb_list = table.column(primary_col).combine_chunks().to_pylist()
    geoms = shapely.from_wkb(wkb_list)
    return shapely.bounds(geoms)


def _hilbert_keys_for_table(table: pa.Table, primary_col: str, total_bounds) -> np.ndarray:
    from vecorel_cli.vecorel.hilbert import hilbert_distances_from_bounds

    bounds = _bounds_array_for_table(table, primary_col)
    return hilbert_distances_from_bounds(bounds, total_bounds)


def _build_output_schema(input_schema: pa.Schema, merged_bbox, geom_types) -> pa.Schema:
    """Patch the geo metadata: merged bbox + union of geometry_types. Other
    schema metadata and field metadata are preserved unchanged."""
    meta = dict(input_schema.metadata or {})
    geo = json.loads(meta[GEO_META_KEY])
    primary_col = geo["primary_column"]
    if merged_bbox is not None:
        geo["columns"][primary_col]["bbox"] = [float(v) for v in merged_bbox]
    if geom_types:
        geo["columns"][primary_col]["geometry_types"] = list(geom_types)
    meta[GEO_META_KEY] = json.dumps(geo).encode("utf-8")
    return input_schema.with_metadata(meta)


def _streaming_merge(
    paths: list,
    output_file: str,
    primary_col: str,
    total_bounds,
    merged_bbox,
    geom_types,
    batch_size: int,
    compression: str,
    compression_level: Optional[int],
) -> None:
    pq_files = [pq.ParquetFile(p) for p in paths]
    in_schema = pq_files[0].schema_arrow
    out_schema = _build_output_schema(in_schema, merged_bbox, geom_types)

    iters = [pf.iter_batches(batch_size=batch_size) for pf in pq_files]
    heads: list = [None] * len(paths)
    hilberts: list = [None] * len(paths)

    def refill(i):
        # Skip any empty batches; mark the iterator exhausted only when next() raises.
        while True:
            try:
                batch = next(iters[i])
            except StopIteration:
                heads[i] = None
                hilberts[i] = None
                return
            if batch.num_rows == 0:
                continue
            tbl = pa.Table.from_batches([batch])
            heads[i] = tbl
            hilberts[i] = _hilbert_keys_for_table(tbl, primary_col, total_bounds)
            return

    for i in range(len(paths)):
        refill(i)

    write_kwargs = {"compression": compression}
    if compression_level is not None:
        write_kwargs["compression_level"] = compression_level
    writer = pq.ParquetWriter(output_file, out_schema, **write_kwargs)

    try:
        while any(h is not None for h in heads):
            active = [i for i, h in enumerate(heads) if h is not None]
            # The horizon is the smallest "current max" Hilbert across active heads.
            # Every row with hilbert <= horizon is emit-safe in this round, because
            # no still-pending row from any other file can possibly be less than it.
            horizon = min(hilberts[i][-1] for i in active)

            chunks = []
            chunk_h = []
            for i in active:
                h = hilberts[i]
                cut = int(np.searchsorted(h, horizon, side="right"))
                if cut == 0:
                    continue
                chunks.append(heads[i].slice(0, cut))
                chunk_h.append(h[:cut])
                if cut == heads[i].num_rows:
                    refill(i)
                else:
                    heads[i] = heads[i].slice(cut)
                    hilberts[i] = h[cut:]

            if not chunks:
                # Defensive: shouldn't happen because at least the file defining the
                # horizon will contribute its full current batch.
                break

            combined = pa.concat_tables(chunks)
            combined_h = np.concatenate(chunk_h)
            order = np.argsort(combined_h, kind="stable")
            writer.write_table(combined.take(pa.array(order)))
    finally:
        writer.close()
