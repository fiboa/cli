import json
import pyarrow.types as pat

from .types import PA_TYPE_CHECK
from .jsonschema import create_jsonschema
from .util import create_validator, get_collection, log as log_, log_extensions, load_datatypes, load_file, load_fiboa_schema, load_parquet_data, load_parquet_schema, merge_schemas, parse_metadata, load_collection_schema, load_geoparquet_schema
from .validate_data import validate_column

def log(text: str, status="info", bullet = True):
    # Indent logs
    prefix = "  - " if bullet else "    "
    log_(prefix + str(text), status)


def validate(file, config):
    if file.endswith(".json") or file.endswith(".geojson"):
        return validate_geojson(file, config)
    else:
        return validate_parquet(file, config)


def validate_collection(collection, config):
    valid = True

    collection_version = collection.get("fiboa_version")
    config_version = config.get("fiboa_version")

    # Check fiboa version
    if not isinstance(collection_version, str):
        log("No fiboa_version string found in collection metadata", "error")
        valid = False

    log("fiboa version: " + config_version)

    if isinstance(collection_version, str) and collection_version != config_version:
        log(f"fiboa versions differs: Collection is {collection_version} and requested specification version is {config_version}", "warning")

    # Check STAC Collection
    if not validate_colletion_schema(collection):
        valid = False

    # Check extensions
    extensions = {}
    if "fiboa_extensions" in collection:
        ext_list = collection.get("fiboa_extensions")
        if not isinstance(ext_list, list):
            log("fiboa_extensions must be a list", "error")
            valid = False
        else:
            ext_map = config.get("extension_schemas", [])
            for ext in ext_list:
                try:
                    if ext in ext_map:
                        path = ext_map[ext]
                        log(f"Redirecting {ext} to {path}", "info")
                    else:
                        path = ext
                    extensions[ext] = load_file(path)
                except Exception as e:
                    log(f"Extension {ext} can't be loaded: {e}", "error")
                    valid = False

    log_extensions(collection, lambda x: log(x, "info", False))

    return valid, extensions


def validate_geojson(file, config):
    valid = True
    extensions = {}

    try:
        data = load_file(file)
    except Exception as error:
        log(error, "error")
        return False

    collection = get_collection(data, config.get("collection"), file)
    if collection is None:
        log("No collection specified", "error")
        valid = False

    if config.get("fiboa_version") is None and collection.get("fiboa_version") is not None:
        config["fiboa_version"] = collection.get("fiboa_version")

    if collection is not None:
        collection_valid, extensions = validate_collection(collection, config)
        if not collection_valid:
            valid = False

    core_schema = load_fiboa_schema(config)
    datatypes = load_datatypes(config["fiboa_version"])
    schema = create_jsonschema(core_schema, datatypes)

    # Load extensions
    ext_errors = []
    for ext in extensions:
        try:
            uri = ext
            if ext in config["extension_schemas"]:
                uri = config["extension_schemas"][ext]
            ext_schema = load_file(uri)
            json_schema = create_jsonschema(ext_schema, datatypes)
            extensions[ext] = lambda obj: validate_json_schema(obj, json_schema)
        except Exception as error:
            extensions[ext] = None
            ext_errors.append(f"Failed to load extension {ext}: {str(error)}")

    for error in ext_errors:
        log(error, "error")

    # Validate
    if not isinstance(data, dict):
        log("Must be a JSON object", "error")
        return False

    if data["type"] == "Feature":
        features = [data]
    elif data["type"] == "FeatureCollection":
        features = data["features"]
    elif data["type"] == "Collection":
        # Skipping specific checks related to STAC Collection
        return None
    else:
        log("Must be a GeoJSON Feature or FeatureCollection", "error")
        return False

    if len(features) == 0:
        log("Must contain at least one Feature", "error")
        return False

    for index, feature in enumerate(features):
        errors = validate_json_schema(feature, schema)
        if len(errors) > 0:
            valid = False

        label = feature.get("id", f"index: {index}")

        if not valid:
            for error in errors:
                log(f"{label}: {error}", "error")
        else:
            for ext, validate_fn in extensions.items():
                if validate_fn:
                    ext_errors = validate_fn(feature)
                    if len(ext_errors) > 0:
                        for error in ext_errors:
                            log(f"{label} (ext {ext}): {error}", "error")
                        valid = False
                else:
                    log(f"{label}: Extension {ext} SKIPPED", "warning")
            if valid and len(features) > 1:
                log(f"{label}: VALID", "success")

    return valid


def validate_parquet(file, config):
    parquet_schema = load_parquet_schema(file)
    valid = True
    extensions = {}

    # Validate geo metadata in Parquet header
    if b"geo" not in parquet_schema.metadata:
        log("Parquet file schema does not have 'geo' key", "error")
        valid = False
    else:
        geo = parse_metadata(parquet_schema, b"geo")
        if not validate_geoparquet_schema(geo):
            valid = False

    # Validate fiboa metadata in Parquet header
    collection = {}
    if b"fiboa" not in parquet_schema.metadata:
        log("Parquet file schema does not have a 'fiboa' key", "warning")
        if not config.get("collection"):
            log("No collection specified", "error")
            valid = False
        else:
            collection = load_file(config.get("collection"))
    else:
        collection = parse_metadata(parquet_schema, b"fiboa")

    if config.get("fiboa_version") is None and collection.get("fiboa_version") is not None:
        config["fiboa_version"] = collection.get("fiboa_version")

    # Validate Collection
    if len(collection) > 0:
        valid_collection, extensions = validate_collection(collection, config)
        if not valid_collection:
            valid = False

    # load the actual fiboa schema
    fiboa_schema = load_fiboa_schema(config)

    # Load data if needed
    gdf = None
    if config.get("data"):
        try:
            gdf = load_parquet_data(file)
        except Exception as e:
            log(f"Data could not be read: {e}", "error")
            valid = False

    # Compile all properties from the schemas
    schemas = fiboa_schema
    for ext in extensions.values():
        schemas = merge_schemas(schemas, ext)

    # Check that all required fields are present
    for key in schemas.get("required", []):
        if key not in parquet_schema.names:
            log(f"{key}: Required field is missing", "error")
            valid = False

    # Validate whether the Parquet schema complies with the property schemas
    properties = schemas.get("properties", {})
    for key in parquet_schema.names:
        # Ignore fields without a schema
        if key not in properties:
            log(f"{key}: No schema defined", "warning")
            continue

        prop_schema = properties[key]
        # Make sure the schema has a data type assigned
        dtype = prop_schema.get("type")
        if dtype is None:
            log(f"{key}: No type specified", "warning")
            continue

        pq_field = parquet_schema.field(key)
        pq_type = pq_field.type

        # Does the field (dis)allow null?
        nullable = key not in schemas.get("required", [])
        if nullable != pq_field.nullable:
            log(f"{key}: Nullability differs, is {pq_field.nullable} but must be {nullable}", "error")
            valid = False

        # Is the data type of the field correct?
        pa_check = PA_TYPE_CHECK.get(dtype)
        if pa_check is None:
            log(f"{key}: Validating {dtype} is not supported yet", "warning")
            continue
        elif not pa_check(pq_type):
            log(f"{key}: Data type invalid, is {pq_type} but must be {dtype}", "error")
            valid = False
            continue

        # Check specifics of some types
        if dtype == "date-time":
            if pq_type.unit != "ms":
                log(f"{key}: Timestamp unit differs, should be ms", "warning")
            if pq_type.tz != "UTC":
                log(f"{key}: Timestamp timezone invalid, must be UTC", "error")
                valid = False
        elif dtype == "object":
            if pat.is_map(pq_type) and not pat.is_string(pq_field.key_type):
                log(f"{key}: Map keys must be strings", "error")
                valid = False
        elif dtype == "geometry":
            valid = validate_geometry_column(key, prop_schema, geo, valid)

        # Validate data of the column
        if gdf is not None:
            issues = validate_column(gdf[key], prop_schema)
            if len(issues) > 0:
                for issue in issues:
                    log(f"{key}: {issue}")
                valid = False

    # Show a note once if data was not validated
    if not config.get("data"):
        log("Data was not validated as the --data parameter was not provided", "info")

    return valid


def validate_geometry_column(key, prop_schema, geo, valid = True):
    columns = geo.get("columns", {})
    if key not in columns:
        log(f"{key}: Geometry column not found in GeoParquet metadata", "error")
        valid = False

    schema_geo_types = prop_schema.get("geometryTypes", [])
    schema_geo_types.sort()
    if len(schema_geo_types) > 0:
        gp_geo_types = columns[key].get("geometry_types", [])
        gp_geo_types.sort()
        if len(gp_geo_types) == 0:
            log(f"{key}: No geometry types specified in GeoParquet metadata", "warning")

        if schema_geo_types != gp_geo_types:
            log(f"{key}: GeoParquet geometry types differ, is {gp_geo_types} but must be {schema_geo_types}", "error")
            valid = False

    return valid

# todo: use stac_validator instead of our own validation routine
def validate_colletion_schema(obj):
    if "stac_version" in obj:
        try:
            schema = load_collection_schema(obj)
            errors = validate_json_schema(obj, schema)
            for error in errors:
                log(f"Collection: {error.path}: {error.message}", "error")

            return len(errors) == 0
        except Exception as e:
            log(f"Failed to validate STAC Collection due to an internal error: {e}", "warning")

    return True


# todo: use a geoparquet validator instead of our own validation routine
def validate_geoparquet_schema(obj):
    if "version" in obj:
        try:
            schema = load_geoparquet_schema(obj)
            errors = validate_json_schema(obj, schema)
            for error in errors:
                log(f"GeoParquet metadata: {error.path}: {error.message}", "error")

            return len(errors) == 0
        except Exception as e:
            log(f"Failed to validate GeoParquet metadata due to an internal error: {e}", "error")

    return False

def validate_json_schema(obj, schema):
    if isinstance(obj, (bytearray, bytes, str)):
        obj = json.loads(obj)

    validator = create_validator(schema)
    errors = sorted(validator.iter_errors(obj), key=lambda e: e.path)
    return errors
