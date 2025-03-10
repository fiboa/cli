import json

import pyarrow.types as pat

from .jsonschema import create_jsonschema
from .types import PA_TYPE_CHECK
from .util import (
    create_validator,
    get_core_version,
    load_datatypes,
    load_file,
    load_geoparquet_schema,
    load_parquet_data,
    load_parquet_schema,
    log_extensions,
    merge_schemas,
    parse_metadata,
)
from .util import log as log_
from .validate_data import validate_column
from .version import is_supported, supported_fiboa_versions


def log(text: str, status="info", bullet=True):
    # Indent logs
    prefix = "  - " if bullet else "    "
    log_(prefix + str(text), status)


def validate(file, config):
    if file.endswith(".json") or file.endswith(".geojson"):
        return validate_geojson(file, config)
    else:
        return validate_parquet(file, config)


def validate_schemas(schema_uris, config):
    valid = True

    if not isinstance(schema_uris, list):
        log("A list of schemas must be provied", "error")
        valid = False

    if len(schema_uris) == 0:
        log("No schemas provided", "error")
        valid = False

    # Detect and check fiboa version
    version = None
    core_schema = None
    for schema_uri in schema_uris:
        version = get_core_version(schema_uri)
        if version is not None:
            core_schema = schema_uri
            break

    if version is None:
        log("fiboa core schema not found in schemas, can't detect fiboa version", "error")
        valid = False

    # todo: use python-semanticversion to check for version ranges (e.g. allow 0.3.x)
    if is_supported(version):
        log(
            f"fiboa versions differs: Schema reports {version} and supported version is {supported_fiboa_versions}",
            "warning",
        )

    # Check schemas (core and extensions)
    schemas = {}
    schema_map = config.get("schemas", {})
    for uri in schema_uris:
        try:
            if uri in schema_map:
                actual_location = schema_map[uri]
                log(f"Redirecting {uri} to {actual_location}", "info")
            else:
                actual_location = uri

            schemas[schema_uri] = load_file(actual_location)
        except Exception as e:
            log(f"Extension {uri} can't be loaded: {e}", "error")
            valid = False

    log_extensions(schema_uris, lambda x: log(x, "info", False))

    return valid, version, core_schema, schemas


def validate_geojson(file, config):
    try:
        data = load_file(file)
    except Exception as error:
        log(error, "error")
        return False

    if not isinstance(data, dict):
        log("Must be a JSON object", "error")
        return False

    schemas_uris = {}
    collection = {}
    feature_type = data.get("type")
    if feature_type == "FeatureCollection":
        collection = data.get("fiboa", {})
        schemas_uris = collection.get("schemas", {})
        features = data["features"]
    elif feature_type == "Feature":
        schemas_uris = data.get("properties", {}).get("schemas", {})
        features = [data]
    else:
        log("Must be a GeoJSON Feature or FeatureCollection", "error")
        return False

    valid, version, core_schema_uri, schemas = validate_schemas(schemas_uris, config)

    core_schema = schemas[core_schema_uri]
    datatypes = load_datatypes(version)
    schema = create_jsonschema(core_schema, datatypes)

    # Load extensions
    ext_errors = []
    extensions = {}
    for ext in schemas:
        try:
            json_schema = create_jsonschema(schemas[ext], datatypes)
            extensions[ext] = lambda obj: validate_json_schema(obj, json_schema)
        except Exception as error:
            extensions[ext] = None
            ext_errors.append(f"Failed to load extension {ext}: {str(error)}")

    for error in ext_errors:
        log(error, "error")

    # Validate
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

    # Validate geo metadata in Parquet header
    if b"geo" not in parquet_schema.metadata:
        log("Parquet file schema does not have 'geo' key", "error")
        return False
    else:
        geo = parse_metadata(parquet_schema, b"geo")
        if not validate_geoparquet_schema(geo):
            return False

    # Validate fiboa metadata in Parquet header
    if b"fiboa" not in parquet_schema.metadata:
        log("Parquet file schema does not have a 'fiboa' key", "error")
        return False

    collection = parse_metadata(parquet_schema, b"fiboa")
    schemas_uris = collection.get("schemas", {})

    valid, version, core_schema_uri, schemas = validate_schemas(schemas_uris, config)

    fiboa_schema = schemas[core_schema_uri]

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
    for ext in schemas.values():
        if core_schema_uri == ext:
            continue
        schemas = merge_schemas(schemas, ext)

    # Add custom schemas
    custom_schemas = collection.get("fiboa_custom_schemas", {})
    schemas = merge_schemas(schemas, custom_schemas)

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
            log(
                f"{key}: Nullability differs, is {pq_field.nullable} but must be {nullable}",
                "error",
            )
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


def validate_geometry_column(key, prop_schema, geo, valid=True):
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
            log(
                f"{key}: GeoParquet geometry types differ, is {gp_geo_types} but must be {schema_geo_types}",
                "error",
            )
            valid = False

    return valid


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
