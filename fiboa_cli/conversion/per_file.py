import json
import os
from pathlib import Path
from typing import Optional

import duckdb
import pyarrow.parquet as pq
from vecorel_cli.conversion.duckdb import DuckDBBaseConverter, _sql_path
from vecorel_cli.encoding.geoparquet import GeoParquet
from vecorel_cli.vecorel.hilbert import hilbert_reference_bounds

from .fiboa_converter import FiboaBaseConverter

GEO_META_KEY = b"geo"
COLLECTION_META_KEY = b"collection"

# The two steps that put a written Parquet file into canonical Hilbert order.
# They are private on the DuckDB converter; vecorel/cli#34 asks for them to
# become shared API, so that one routine orders every file we write.
_write_hilbert_keys = DuckDBBaseConverter._write_hilbert_keys
_sort_output = DuckDBBaseConverter._sort_output


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
            part = os.path.join(dirname, f"{filename}_{index}_part{ext}")
            part_files.append(part)
            if os.path.exists(part):
                self.info(
                    f"Skipping existing file {part}: {uri} -> {output_file} (part {index + 1}/{len(urls)})"
                )
                continue
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
        self.merge_files(
            output_file,
            part_files,
            compression=compression or "zstd",
            compression_level=compression_level,
            geoparquet_version=geoparquet_version,
            cleanup_parts=True,
        )
        return output_file

    def merge_files(
        self,
        output_file: str,
        paths: list,
        compression: str = "zstd",
        compression_level: Optional[int] = None,
        geoparquet_version: Optional[str] = None,
        cleanup_parts: bool = False,
    ) -> str:
        """
        Merge GeoParquet parts into one file, sorted into the canonical Hilbert
        order over the merged extent, so the ordering does not depend on which
        part a feature came from.

        The parts are concatenated and sorted by DuckDB, which sorts externally
        and spills to disk, and packaged by ``GeoParquet.postprocess`` — the same
        two steps the DuckDB converter uses, so this writes no Parquet of its own.
        """
        if not paths:
            raise ValueError("No paths to merge")
        paths = [str(p) for p in paths]

        geo, collection_json, expected_rows = self._merged_metadata(paths)
        primary = geo["primary_column"]
        crs = geo["columns"][primary].get("crs")
        bounds = hilbert_reference_bounds(crs, geo["columns"][primary].get("bbox"))
        if bounds is None:
            raise ValueError(
                f"Cannot order {output_file}: its CRS declares no area of use and the "
                "parts carry no bbox to fall back on"
            )

        if isinstance(output_file, Path):
            output_file = str(output_file)
        directory = os.path.dirname(output_file) or "."

        con = duckdb.connect()
        con.install_extension("spatial")
        con.load_extension("spatial")
        # Sorting a dataset that does not fit in memory spills; keep that next to
        # the output rather than in a /tmp that is usually far smaller
        con.execute(f"SET temp_directory = {_sql_path(os.path.join(directory, '.duckdb_tmp'))}")

        self.info(f"Merging {len(paths)} part(s) -> {output_file} (Hilbert bounds {bounds})")
        sources = "[" + ",".join(_sql_path(path) for path in paths) + "]"
        con.execute(
            f"""
            COPY (SELECT * FROM read_parquet({sources})) TO ? (
                FORMAT parquet,
                ROW_GROUP_SIZE {GeoParquet.row_group_size},
                compression ?,
                KV_METADATA {{ geo: ?, collection: ? }}
            )
            """,
            [output_file, compression, json.dumps(geo).encode("utf-8"), collection_json],
        )

        keys_path, is_sorted = _write_hilbert_keys(self, output_file, primary, bounds)
        try:
            if not is_sorted:
                _sort_output(
                    self,
                    con,
                    output_file,
                    keys_path,
                    compression,
                    collection_json,
                    GeoParquet.row_group_size,
                )
        finally:
            if os.path.exists(keys_path):
                os.unlink(keys_path)

        gp = GeoParquet(Path(output_file))
        gp.postprocess(
            compression=compression,
            compression_level=compression_level,
            geoparquet_version=geoparquet_version,
            crs=crs,
        )

        actual_rows = _num_rows(output_file)
        if actual_rows != expected_rows:
            raise RuntimeError(
                f"Merge lost rows: expected {expected_rows:,} (sum of the parts), "
                f"wrote {actual_rows:,} to {output_file}"
            )
        self.info(f"Merged {actual_rows:,} rows into {output_file}")

        if cleanup_parts:
            for path in paths:
                try:
                    os.remove(path)
                except OSError:
                    self.warning(f"Could not remove part file {path}")

        return output_file

    def _merged_metadata(self, paths: list):
        """The geo metadata of the merged file: one schema and one CRS for every
        part, the union of their extents and geometry types."""
        with pq.ParquetFile(paths[0]) as pf:
            base_schema = pf.schema_arrow
            rows = pf.metadata.num_rows
        base_meta = base_schema.metadata or {}
        if GEO_META_KEY not in base_meta:
            raise ValueError(f"{paths[0]} has no 'geo' metadata; not a GeoParquet?")
        geo = json.loads(base_meta[GEO_META_KEY])
        primary = geo["primary_column"]
        column = geo["columns"][primary]
        crs = column.get("crs")

        bboxes = [column["bbox"]] if column.get("bbox") is not None else []
        geom_types = set(column.get("geometry_types") or [])
        for path in paths[1:]:
            with pq.ParquetFile(path) as pf:
                schema = pf.schema_arrow
                rows += pf.metadata.num_rows
            if not schema.equals(base_schema, check_metadata=False):
                raise ValueError(
                    f"Schema mismatch: {path} differs from {paths[0]}.\n"
                    f"  Expected: {base_schema}\n"
                    f"  Got:      {schema}"
                )
            part = json.loads((schema.metadata or {})[GEO_META_KEY])["columns"][primary]
            if part.get("crs") != crs:
                raise ValueError(
                    f"CRS mismatch: {path} has crs={part.get('crs')!r}, expected {crs!r}"
                )
            if part.get("bbox") is not None:
                bboxes.append(part["bbox"])
            geom_types.update(part.get("geometry_types") or [])

        if bboxes:
            column["bbox"] = [
                min(b[0] for b in bboxes),
                min(b[1] for b in bboxes),
                max(b[2] for b in bboxes),
                max(b[3] for b in bboxes),
            ]
        if geom_types:
            column["geometry_types"] = sorted(geom_types)
        return geo, base_meta.get(COLLECTION_META_KEY, b"{}"), rows


def _num_rows(path) -> int:
    with pq.ParquetFile(path) as pf:
        return pf.metadata.num_rows
