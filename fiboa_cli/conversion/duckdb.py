import json
import os

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

        selection = ", ".join(selections)
        if isinstance(urls, str):
            sources = f'"{urls}"'
        else:
            sources = "[" + ",".join([f'"{url}"' for url in urls]) + "]"

        _collection = self.create_collection(cid)
        _collection.update(self.column_additions)
        collection = json.dumps(_collection, cls=VecorelJSONEncoder).encode("utf-8")

        # TODO how to get metadata ARROW:schema ?
        # from vecorel_cli.parquet.types import get_pyarrow_field
        # schemas = _collection.merge_schemas({})
        # props = schemas.get("properties", {})
        # pq_fields = []
        # for column in self.columns.values():
        #     schema = props.get(column, {})
        #     dtype = schema.get("type")
        #     if dtype is None:
        #         self.warning(f"{column}: No mapping")
        #         continue
        #     try:
        #         field = get_pyarrow_field(column, schema=schema)
        #         pq_fields.append(field)
        #     except Exception as e:
        #         self.warning(f"{column}: Skipped - {e}")
        #
        # pq_schema = pa.schema(pq_fields)
        # pq_schema = pq_schema.with_metadata({"collection": collection})

        con = duckdb.connect()
        con.install_extension("spatial")
        con.load_extension("spatial")
        con.execute(
            f"""
            COPY (
              SELECT {selection} FROM read_parquet({sources})
              {where}
              ORDER BY ST_Hilbert({geom_column})
            ) TO ? (
                FORMAT parquet,
                compression 'brotli',
                KV_METADATA {{
                    collection: ?,
                }}
            )
        """,
            [output_file, collection],
        )

        return output_file
