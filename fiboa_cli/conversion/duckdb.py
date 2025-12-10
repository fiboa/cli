import json
import os
from pathlib import Path

import duckdb
import pyarrow as pa
from vecorel_cli.encoding.geojson import VecorelJSONEncoder
from vecorel_cli.parquet.types import get_pyarrow_field

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
            sources = "[" + ",".join([f'"{url}"' for url in urls]) + "]"

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
                compression '{compression}',
                KV_METADATA {{
                    collection: ?,
                }}
            )
        """,
            [output_file, collection_json],
        )

        return output_file
