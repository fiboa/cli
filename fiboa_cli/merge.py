import os

import pandas as pd

from .const import CORE_COLUMNS
from .parquet import create_parquet
from .util import (
    is_schema_empty,
    load_parquet_data,
    load_parquet_schema,
    log,
    merge_schemas,
    parse_metadata,
    pick_schemas,
)
from .version import fiboa_version

DEFAULT_CRS = "EPSG:4326"


def merge(
    datasets,
    out,
    crs=DEFAULT_CRS,
    includes=[],
    excludes=[],
    extensions=set(),
    compression=None,
    geoparquet1=False,
):
    directory = os.path.dirname(out)
    if directory:
        os.makedirs(directory, exist_ok=True)

    columns = CORE_COLUMNS.copy()
    columns.extend(includes)
    columns = list(set(columns) - set(excludes))

    # Load the datasets
    all_gdf = []
    custom_schemas = {}
    for dataset in datasets:
        # Load the dataset
        schema = load_parquet_schema(dataset)
        collection = parse_metadata(schema, b"fiboa")
        file_columns = list(set(columns) & set(schema.names))
        gdf = load_parquet_data(dataset, columns=file_columns)

        # Change the CRS if necessary
        gdf.to_crs(crs=crs, inplace=True)

        # Add collection column to each dataset
        if collection is not None and "id" in collection:
            gdf["collection"] = collection["id"]
        else:
            gdf["collection"] = os.path.splitext(os.path.basename(dataset))[0]

        # Merge custom schemas
        custom_schema = collection.get("fiboa_custom_schemas", {})
        custom_schemas = merge_schemas(custom_schemas, custom_schema)

        all_gdf.append(gdf)

    merged = pd.concat(all_gdf, ignore_index=True)

    # Remove empty columns
    merged.dropna(axis=1, how="all", inplace=True)
    columns = list(merged.columns)
    columns.sort()

    # Create collection metadata
    collection = {
        "fiboa_version": fiboa_version,
        "fiboa_extensions": list(extensions),
    }

    # Add custom schemas
    custom_schemas = pick_schemas(custom_schemas, columns)
    if not is_schema_empty(custom_schemas):
        collection["fiboa_custom_schemas"] = custom_schemas

    # Write the merged dataset to the output file
    create_parquet(
        merged, columns, collection, out, {}, compression=compression, geoparquet1=geoparquet1
    )
    log(f"Merged data to {out}", "success")
