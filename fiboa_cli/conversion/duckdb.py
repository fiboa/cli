import json
import os
from pathlib import Path

import duckdb
from vecorel_cli.encoding.geojson import VecorelJSONEncoder

from .fiboa_converter import FiboaBaseConverter


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
        if geoparquet_version is not None:
            self.warning("geoparquet_version is not supported for DuckDB-based converters and will always write GeoParquet v1.0")
        if not original_geometries:
            self.warning("original_geometries is not supported for DuckDB-based converters and will always write original geometries")

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
            self.warning("avoid_range_request is set, but cache is not used, so this setting has no effect")

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
            [output_file, compression or 'brotli', collection_json],
        )

        # todo: write the file again to do the following:
        # - update geoparquet version to 1.1
        # - add bounding box + metadata
        # - add the non-nullability to the respective columns
        # Ideally do this in improve...

        return output_file
