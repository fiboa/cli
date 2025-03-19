import os

from .const import CORE_COLUMNS
from .parquet import create_parquet
from .util import (
    is_schema_empty,
    load_parquet_data,
    load_parquet_schema,
    log,
    parse_metadata,
    pick_schemas,
)


def improve(
    input,
    out=None,
    rename_columns={},
    add_sizes=False,
    fix_geometries=False,
    explode_geometries=False,
    crs=None,
    compression=None,
    geoparquet1=False,
):
    # Prepare and determine location of the output file
    if not out:
        out = input
    else:
        directory = os.path.dirname(out)
        if directory:
            os.makedirs(directory, exist_ok=True)

    # Load the dataset
    schema = load_parquet_schema(input)
    collection = parse_metadata(schema, b"fiboa")
    columns = list(schema.names)
    # Remove the bbox column to avoid conflicts when writing GeoParquet file later
    columns.remove("bbox")
    gdf = load_parquet_data(input, columns=columns)

    # Change the CRS
    if crs is not None:
        gdf.to_crs(crs=crs, inplace=True)
        log(f"Changed CRS to {crs}", "info")

    # Fix geometries
    if fix_geometries:
        gdf.geometry = gdf.geometry.make_valid()
        log("Fixed geometries", "info")

    # Convert MultiPolygons to Polygons
    if explode_geometries:
        gdf = gdf.explode()
        log("Exploded geometries", "info")

    # Rename columns
    if len(rename_columns) > 0:
        for col in rename_columns:
            columns[columns.index(col)] = rename_columns[col]
            if col in CORE_COLUMNS:
                log(
                    f"Column {col} is a fiboa core field - do you really want to rename it?",
                    "warning",
                )
            if ":" in col:
                log(
                    f"Column {col} may be a fiboa extension field - do you really want to rename it?",
                    "warning",
                )
        gdf.rename(columns=rename_columns, inplace=True)
        log("Renamed columns", "info")

    # Add sizes
    if add_sizes:
        # Add the area and perimeter columns
        for name in ["area", "perimeter"]:
            if name not in columns:
                # Create column if not present
                gdf[name] = None
                columns.append(name)

        gdf_m = gdf
        # Determine whether the given CRS is in meters
        if gdf.crs.axis_info[0].unit_name not in ["m", "metre", "meter"]:
            # Reproject the geometries to an equal-area projection if needed
            gdf_m = gdf.to_crs("EPSG:6933")

        # Compute the missing area and perimeter values
        gdf["area"] = gdf_m["area"].fillna(gdf_m.geometry.area * 0.0001)
        gdf["perimeter"] = gdf_m["perimeter"].fillna(gdf_m.geometry.length)

    custom_schemas = collection.get("fiboa_custom_schemas", {})
    custom_schemas = pick_schemas(custom_schemas, columns, rename_columns)
    if not is_schema_empty(custom_schemas):
        collection["fiboa_custom_schemas"] = custom_schemas

    # Write the merged dataset to the output file
    create_parquet(
        gdf, columns, collection, out, {}, compression=compression, geoparquet1=geoparquet1
    )
    log(f"Wrote data to {out}", "success")
