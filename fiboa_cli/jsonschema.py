import json

from .jsonschema_template import jsonschema_template
from .util import load_datatypes, load_fiboa_schema, log


def jsonschema(config):
    core_schema = load_fiboa_schema(config)
    datatypes = load_datatypes(config["fiboa_version"])
    return create_jsonschema(core_schema, datatypes, config.get("id"))


def create_jsonschema(core_schema, datatypes, id=None):
    geojson_root_properties = ["id", "geometry", "bbox", "properties"]

    geojson = {
        "root": {"required": [], "properties": {}},
        "properties": {"required": [], "properties": {}},
    }

    for key, prop_schema in core_schema.get("properties", {}).items():
        required = key in core_schema.get("required", [])
        result = convert_schema(prop_schema, datatypes, required)

        place = "root" if key in geojson_root_properties else "properties"
        if required:
            geojson[place]["required"].append(key)
        geojson[place]["properties"][key] = result["schema"]

    schema = jsonschema_template()
    if id:
        schema["$id"] = id
    else:
        schema.pop("$id", None)

    def merge(target, source):
        if "required" in target and isinstance(target["required"], list):
            for prop in source["required"]:
                if prop not in target["required"]:
                    target["required"].append(prop)
        else:
            target["required"] = source["required"]
        if "properties" in target and isinstance(target["properties"], dict):
            target["properties"].update(source["properties"])
        else:
            target["properties"] = source["properties"]

    merge(schema, geojson["root"])
    merge(schema["properties"]["properties"], geojson["properties"])

    return schema


def convert_schema(prop_schema, datatypes, required=False):
    if not isinstance(prop_schema, dict) or "type" not in prop_schema:
        return prop_schema
    elif prop_schema["type"] not in datatypes:
        raise ValueError(f"Unknown datatype {prop_schema['type']}")

    datatype_schema = datatypes[prop_schema["type"]].copy()

    if prop_schema["type"] == "geometry":
        geom_types = prop_schema.get("geometryTypes", [])
        if isinstance(prop_schema.get("geometryTypes"), list):
            datatype_schema = {
                "anyOf": [
                    {"$ref": f"https://geojson.org/schema/{type}.json"} for type in geom_types
                ]
            }
            del prop_schema["geometryTypes"]

    anyOf = datatype_schema.get("anyOf")
    allOf = datatype_schema.get("allOf")
    oneOf = datatype_schema.get("oneOf")
    if required:
        not_null_schema = {"not": {"type": "null"}}

        if "$ref" in datatype_schema or isinstance(anyOf, list) or isinstance(oneOf, list):
            datatype_schema = {"allOf": [datatype_schema, not_null_schema]}
        elif isinstance(allOf, list):
            allOf.append(not_null_schema)

    else:
        schema_type = datatype_schema.get("type")
        null_schema = {"type": "null"}

        if "$ref" in datatype_schema:
            datatype_schema = {"allOf": [datatype_schema, null_schema]}
        elif isinstance(schema_type, str):
            datatype_schema["type"] = [datatype_schema["type"], "null"]
        elif isinstance(schema_type, list):
            datatype_schema["type"].append("null")
        elif isinstance(oneOf, list):
            datatype_schema["oneOf"].append(null_schema)
        elif isinstance(anyOf, list):
            datatype_schema["anyOf"].append(null_schema)
        else:
            log(
                f"Making schema {json.dumps(datatype_schema)} optional is not supported by this generator"
            )

    # Avoid conflicting statements
    if "exclusiveMaximum" in prop_schema:
        datatype_schema.pop("maximum", None)
    if "exclusiveMinimum" in prop_schema:
        datatype_schema.pop("minimum", None)
    if "maximum" in prop_schema:
        datatype_schema.pop("exclusiveMaximum", None)
    if "minimum" in prop_schema:
        datatype_schema.pop("exclusiveMinimum", None)

    # Deep merge schemas
    for key, value in prop_schema.items():
        if key == "items" and isinstance(value, dict):
            result = convert_schema(value, datatypes)
            datatype_schema["items"] = {**datatype_schema.get("items", {}), **result["schema"]}
        elif key == "properties" and isinstance(value, dict):
            if not isinstance(datatype_schema.get("properties"), dict):
                datatype_schema["properties"] = {}
            if not isinstance(datatype_schema.get("required"), list):
                datatype_schema["required"] = []
            for prop_name, prop_value in value.items():
                required = key in value.get("required", [])
                result = convert_schema(prop_value, datatypes, required)
                datatype_schema["properties"][prop_name] = {
                    **datatype_schema["properties"].get(prop_name, {}),
                    **result["schema"],
                }
                if required:
                    datatype_schema["required"].append(prop_name)
        elif key not in ["type", "required"]:
            datatype_schema[key] = value

    return {"required": required, "schema": datatype_schema}
