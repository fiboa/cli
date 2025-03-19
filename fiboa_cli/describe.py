import json

import pandas as pd

from .util import (
    is_schema_empty,
    load_parquet_data,
    load_parquet_metadata,
    load_parquet_schema,
    log,
    log_extensions,
    parse_metadata,
)


def describe(file, display_json=False, num=10, columns=None):
    metadata = load_parquet_metadata(file)

    log("== GEOPARQUET ==", "success")
    geo = parse_metadata(metadata, b"geo")
    geo_columns = []
    if geo:
        log(f"GeoParquet version: {geo['version']}")

        geo_columns = geo.get("columns", {}).keys()
        columns_str = ", ".join(geo_columns)
        log(f"Geometry columns: {columns_str}")

        if display_json:
            log(json.dumps(geo, indent=2))

    log("\n== COLLECTION ==", "success")
    collection = parse_metadata(metadata, b"fiboa")
    if collection:
        log(f"fiboa version: {collection['fiboa_version']}")
        if "fiboa_extensions" in collection and isinstance(collection["fiboa_extensions"], list):
            log_extensions(collection, log)

        custom_schemas = collection.get("fiboa_custom_schemas", {})
        if not is_schema_empty(custom_schemas):
            log("Custom schemas: " + ", ".join(custom_schemas["properties"].keys()))

        if display_json:
            log(json.dumps(collection, indent=2))
        elif "stac_version" in collection:
            log("STAC metadata included, add --json to show it", "warning")

    log(f"\n== SCHEMA (columns: {metadata.num_columns}) ==", "success")
    schema = load_parquet_schema(file)
    log(schema.to_string(show_schema_metadata=False))

    log(f"\n== DATA (rows: {metadata.num_rows}, groups: {metadata.num_row_groups}) ==", "success")
    if num > 0:
        # Make it so that everything is shown, don't output ... if there are too many columns or rows
        pd.set_option("display.max_columns", None)
        pd.set_option("display.max_rows", None)
        # Load data
        geodata = load_parquet_data(file, columns=columns)
        # Print to console
        log(geodata.head(num))
    else:
        log("Omitted")
