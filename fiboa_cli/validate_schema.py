from .util import log as log_, load_file, create_validator

def log(text: str, status="info"):
    # Indent logs
    log_("  - " + str(text), status)


def validate_schema(file, config):
    schema = load_file(file)
    if not isinstance(schema, dict):
        log("Schema must be an object", "error")
        return False

    metaschema_uri = config.get("metaschema")
    if metaschema_uri is None:
        metaschema_uri = schema.get("$schema", metaschema_uri)
    if metaschema_uri is None:
        log("No metaschema provided", "error")
        return False

    log(f"Metaschema: {metaschema_uri}", "info")

    metaschema = load_file(metaschema_uri)

    errors = validate_json_schema(schema, metaschema)
    if len(errors) > 0:
        for error in errors:
            log(error, "error")
        return False
    else:
        log("VALID", "success")
        return True

def validate_json_schema(obj, schema):
    validator = create_validator(schema)
    errors = sorted(validator.iter_errors(obj), key=lambda e: e.path)
    return errors
