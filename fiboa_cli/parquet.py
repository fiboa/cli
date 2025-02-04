import json
import pyarrow as pa

from geopandas import GeoDataFrame
from shapely.geometry import shape

from .types import get_geopandas_dtype, get_pyarrow_type_for_geopandas, get_pyarrow_field
from .util import log, load_fiboa_schema, load_file, merge_schemas, is_schema_empty
from .geopandas import to_parquet

ROW_GROUP_SIZE = 25000

def create_parquet(data, columns, collection, output_file, config, missing_schemas = {}, compression = None, geoparquet1 = False):
    # Load the data schema
    fiboa_schema = load_fiboa_schema(config)
    schemas = merge_schemas(missing_schemas, fiboa_schema)

    # Add the custom schemas to the collection for future use
    if not is_schema_empty(missing_schemas):
        collection = collection.copy()
        collection["fiboa_custom_schemas"] = missing_schemas

    # Load all extension schemas
    extensions = {}
    if "fiboa_extensions" in collection and isinstance(collection["fiboa_extensions"], list):
        ext_map = config.get("extension_schemas", [])
        for ext in collection["fiboa_extensions"]:
            try:
                if ext in ext_map and ext_map[ext] is not None:
                    path = ext_map[ext]
                    log(f"Redirecting {ext} to {path}", "info")
                else:
                    path = ext
                extensions[ext] = load_file(path)
                schemas = merge_schemas(schemas, extensions[ext])
            except Exception as e:
                log(f"Extension schema for {ext} can't be loaded: {e}", "warning")

    # Create GeoDataFrame from the features
    if not isinstance(data, GeoDataFrame):
        data = features_to_dataframe(data, columns)

    # Update the GeoDataFrame with the correct types etc.
    data = update_dataframe(data, columns, schemas)

    _columns = list(data.columns)
    duplicates = set([x for x in _columns if _columns.count(x) > 1])
    if len(duplicates):
        raise ValueError(f"Columns are defined multiple times: {duplicates}")

    # Define the fields for the schema
    pq_fields = []
    for name in columns:
        required_props = schemas.get("required", [])
        properties = schemas.get("properties", {})
        required = name in required_props
        field = None
        if name in properties:
            prop_schema = properties[name]
            try:
                field = get_pyarrow_field(name, schema = prop_schema, required = required)
            except Exception as e:
                log(f"{name}: Skipped - {e}", "warning")
        else:
            pd_type = str(data[name].dtype) # pandas data type
            try:
                pa_type = get_pyarrow_type_for_geopandas(pd_type) # pyarrow data type
                if pa_type is not None:
                    log(f"{name}: No schema defined, converting {pd_type} to nullable {pa_type}", "warning")
                    field = get_pyarrow_field(name, pa_type = pa_type)
                else:
                    log(f"{name}: Skipped - pandas type can't be converted to pyarrow type", "warning")
                    continue
            except Exception as e:
                log(f"{name}: Skipped - {e}", "warning")
                continue

        if field is None:
            log(f"{name}: Skipped - invalid data type", "warning")
            continue
        else:
            pq_fields.append(field)

    # Define the schema for the Parquet file
    pq_schema = pa.schema(pq_fields)
    pq_schema = pq_schema.with_metadata({"fiboa": json.dumps(collection).encode("utf-8")})

    if compression is None:
        compression = "brotli"

    # Write the data to the Parquet file
    to_parquet(
        data,
        output_file,
        schema = pq_schema,
        index = False,
        coerce_timestamps = "ms",
        compression = compression,
        schema_version = "1.0.0" if geoparquet1 else "1.1.0",
        row_group_size = ROW_GROUP_SIZE,
        write_covering_bbox = False if geoparquet1 else True
    )

    return pq_fields


def features_to_dataframe(features, columns):
    # Create a list of shapes
    rows = []
    for feature in features:
        id = feature["id"] if "id" in feature else None
        geometry = shape(feature["geometry"]) if "geometry" in feature else None
        row = {
            "id": id,
            "geometry": geometry,
        }
        properties = feature["properties"] if "properties" in feature else {}
        row.update(properties)
        rows.append(row)

    # Create the GeoDataFrame
    return GeoDataFrame(rows, columns=columns, geometry="geometry", crs="EPSG:4326")


def update_dataframe(data, columns, schema):
    # Convert the data to the correct types
    properties = schema.get("properties", {})
    required_props = schema.get("required", [])
    for column in columns:
        if column not in properties:
            continue
        schema = properties[column]
        dtype = schema.get("type")
        if dtype == "geometry":
            continue

        required = column in required_props
        gp_type = get_geopandas_dtype(dtype, required, schema)
        try:
            if gp_type is None:
                log(f"{column}: No type conversion available for {dtype}")
            elif callable(gp_type):
                data[column] = gp_type(data[column])
            else:
                data[column] = data[column].astype(gp_type, copy = False)
        except Exception as e:
            log(f"{column}: Can't convert to {dtype}: {e}", "warning")

    return data
