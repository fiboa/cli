def jsonschema_template():
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "",
        "type": "object",
        "required": ["properties"],
        "properties": {"id": {}, "geometry": {}, "bbox": {}, "properties": {"type": "object"}},
        "allOf": [{"$ref": "https://geojson.org/schema/Feature.json"}],
    }
