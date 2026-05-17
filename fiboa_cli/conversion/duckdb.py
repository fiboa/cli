import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from geopandas.array import from_wkb
from pyarrow.lib import StructArray
from vecorel_cli.encoding.geojson import VecorelJSONEncoder

from .fiboa_converter import FiboaBaseConverter


# This converter is experimental, use with caution.
# Results may not be fully fiboa compliant yet.
# Use this primarily for datasets that are too large to be processed by the default converter
class FiboaDuckDBBaseConverter(FiboaBaseConverter):
    def convert(
        self,
        output_file,
        cache=None,
        input_files=None,
        variant=None,
        compression=None,
        geoparquet_version=None,
        original_geometries=False,
        **kwargs,
    ) -> str:
        if not original_geometries:
            self.warning(
                "original_geometries is not supported for DuckDB-based converters and will always write original geometries"
            )

        geoparquet_version = geoparquet_version or "1.1.0"
        compression = compression or "brotli"

        self.variant = variant
        cid = self.id.strip()
        if self.bbox is not None and len(self.bbox) != 4:
            raise ValueError("If provided, the bounding box must consist of 4 numbers")

        # Create output folder if it doesn't exist
        directory = os.path.dirname(output_file)
        if directory:
            os.makedirs(directory, exist_ok=True)

        if input_files is not None and isinstance(input_files, dict) and len(input_files) > 0:
            self.warning("Using user provided input file(s) instead of the pre-defined file(s)")
            urls = input_files
        else:
            urls = self.get_urls()
            if urls is None:
                raise ValueError("No input files provided")

        self.info("Getting file(s) if not cached yet")
        if cache:
            request_args = {}
            if self.avoid_range_request:
                request_args["block_size"] = 0
            urls = self.download_files(urls, cache, **request_args)
        elif self.avoid_range_request:
            self.warning(
                "avoid_range_request is set, but cache is not used, so this setting has no effect"
            )

        selections = []
        geom_column = None
        for k, v in self.columns.items():
            if k in self.column_migrations:
                selections.append(f'{self.column_migrations.get(k)} as "{v}"')
            else:
                selections.append(f'"{k}" as "{v}"')
            if v == "geometry":
                geom_column = k
        selection = ", ".join(selections)

        filters = []
        where = ""
        if self.bbox is not None:
            filters.append(
                f"ST_Intersects(geometry, ST_MakeEnvelope({self.bbox[0]}, {self.bbox[1]}, {self.bbox[2]}, {self.bbox[3]}))"
            )
        for k, v in self.column_filters.items():
            filters.append(v)
        if len(filters) > 0:
            where = f"WHERE {' AND '.join(filters)}"

        if isinstance(urls, str):
            sources = f'"{urls}"'
        else:
            paths = []
            for url in urls:
                if isinstance(url, tuple):
                    paths.append(f'"{url[0]}"')
                else:
                    paths.append(f'"{url}"')
            sources = "[" + ",".join(paths) + "]"

        collection = self.create_collection(cid)
        collection.update(self.column_additions)
        collection["collection"] = self.id

        if isinstance(output_file, Path):
            output_file = str(output_file)

        collection_json = json.dumps(collection, cls=VecorelJSONEncoder).encode("utf-8")

        con = duckdb.connect()
        con.install_extension("spatial")
        con.load_extension("spatial")
        con.execute(
            f"""
            COPY (
              SELECT {selection}
              FROM read_parquet({sources}, union_by_name=true)
              {where}
              ORDER BY ST_Hilbert({geom_column})
            ) TO ? (
                FORMAT parquet,
                compression ?,
                KV_METADATA {{
                    collection: ?,
                }}
            )
        """,
            [output_file, compression, collection_json],
        )

        # Post-process the written Parquet to proper GeoParquet v1.1 with bbox and nullability
        try:
            pq_file = pq.ParquetFile(output_file)

            existing_schema = pq_file.schema_arrow
            col_names = existing_schema.names
            assert "geometry" in col_names, "Missing geometry column in output parquet file"

            schemas = collection.merge_schemas({})
            collection_only = {k for k, v in schemas.get("collection", {}).items() if v}
            required_columns = {"geometry"} | {
                r
                for r in schemas.get("required", [])
                if r in col_names and r not in collection_only
            }
            if "id" in col_names:
                required_columns.add("id")

            # Update for version 1.1.0
            metadata = existing_schema.metadata
            if geoparquet_version > "1.0.0":
                geo_meta = json.loads(existing_schema.metadata[b"geo"])
                geo_meta["version"] = geoparquet_version
                metadata[b"geo"] = json.dumps(geo_meta).encode("utf-8")

            # Build a new Arrow schema with adjusted nullability
            new_fields = []
            for field in existing_schema:
                if field.name in required_columns and field.nullable:
                    new_fields.append(
                        pa.field(field.name, field.type, nullable=False, metadata=field.metadata)
                    )
                else:
                    new_fields.append(field)

            add_bbox = geoparquet_version > "1.0.0" and "bbox" not in col_names
            if add_bbox:
                new_fields.append(
                    pa.field(
                        "bbox",
                        pa.struct(
                            [
                                ("xmin", pa.float64()),
                                ("ymin", pa.float64()),
                                ("xmax", pa.float64()),
                                ("ymax", pa.float64()),
                            ]
                        ),
                    )
                )
            new_schema = pa.schema(new_fields, metadata=metadata)

            # 7) Streamingly rewrite the file to a temp file and replace atomically
            with NamedTemporaryFile(
                "wb", delete=False, dir=os.path.dirname(output_file), suffix=".parquet"
            ) as tmp:
                tmp_path = tmp.name

            writer = pq.ParquetWriter(
                tmp_path,
                new_schema,
                compression=compression,
                use_dictionary=True,
                write_statistics=True,
            )
            try:
                bbox_names = ["ymax", "xmax", "ymin", "xmin"]
                for rg in range(pq_file.num_row_groups):
                    tbl = pq_file.read_row_group(rg)
                    if add_bbox:
                        # determine bounds, change to StructArray type
                        bounds = from_wkb(tbl["geometry"]).bounds
                        bbox_array = StructArray.from_arrays(
                            np.rot90(bounds),
                            names=bbox_names,
                        )
                        tbl = tbl.append_column("bbox", bbox_array)
                    # Ensure table adheres to the new schema (mainly nullability); cast if needed
                    if tbl.schema != new_schema:
                        # Align field order/types; this does not materialize data beyond the batch
                        tbl = tbl.cast(new_schema, safe=False)
                    writer.write_table(tbl)
            finally:
                writer.close()

            os.replace(tmp_path, output_file)
        except Exception as e:
            self.warning(f"GeoParquet 1.1 post-processing failed: {e}")

        return output_file
