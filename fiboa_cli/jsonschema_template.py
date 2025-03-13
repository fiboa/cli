# fmt: off

def jsonschema_template(properties: dict, required: list, id_ = None):
    # The properties that are defined in fiboa, but are also GeoJSON top-level properties
    geojson_props = ["id", "geometry", "bbox"]
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "if": {
            # Check whether the GeoJSON is a FeatureCollection, otherwise it must be a Feature
            "type": "object",
            "required": ["type"],
            "properties": {
                "type": {
                    "const": "FeatureCollection"
                }
            }
        },
        "then": {
            # Schema for Feature Collections
            "type": "object",
            "allOf": [
                {"$ref": "https://geojson.org/schema/FeatureCollection.json"},
                {"$ref": "#/$defs/featurecollection_requirements"},
                {"$ref": "#/$defs/featurecollection_uniquenesss"},
                {"$ref": "#/$defs/featurecollection_schemas"}
            ]
        },
        "else": {
            # Schema for Features
            "allOf": [
                {"$ref": "https://geojson.org/schema/Feature.json"},
                {"$ref": "#/$defs/feature_requirements"},
                {"$ref": "#/$defs/feature_schemas"}
            ]
        },
        "$defs": {
            "feature_requirements": {
                # Features: Require specific properties in properties
                "type": "object",
                "properties": {
                    "properties": {
                        "type": "object",
                        "required": [
                            key for key in required if key not in geojson_props
                        ]
                    }
                }
            },
            "feature_schemas": {
                # Features: Schemas, but without requiring specific properties in properties
                "type": "object",
                # We assume here that the core GeoJSON properties are never moved to the collection-level data
                "required": [
                    key for key in required if key in geojson_props
                ],
                "properties": {
                    "id": properties.get("id", {}),
                    "geometry": properties.get("geometry", {}),
                    "bbox": properties.get("bbox", {}),
                    "properties": {
                        "type": "object",
                        "properties": {
                            key: properties[key] for key in properties if key not in geojson_props
                        }
                    }
                },
            },
            "featurecollection_uniquenesss": {
                # FeatureCollection: Ensure that collection properties are never provided in the features
                "allOf": [
                    {
                        "if": {
                            # Check whether the property exists in the collection
                            "type": "object",
                            "required": [key]
                        },
                        "then": {
                            # Don't allow this property in the features
                            "type": "object",
                            "properties": {
                                "features": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "properties": {
                                                "type": "object",
                                                "not": {
                                                    "required": [key]
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    } for key in properties if key not in geojson_props
                ]
            },
            "featurecollection_requirements": {
                # FeatureCollection: Require properties either in the collection or in each features
                "allOf": [
                    {
                        "if": {
                            # Check whether the property exists in the collection
                            "type": "object",
                            "required": [key]
                        },
                        "then": {
                            # Check whether the property exists in the each feature in the properties
                            "type": "object",
                            "properties": {
                                "features": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "properties": {
                                                "type": "object",
                                                "required": [key]
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    } for key in required if key not in geojson_props
                ]
            },
            "featurecollection_schemas": {
                # FeatureCollection: Check each feature against the schemas without requiring specific properties in properties
                "type": "object",
                "properties": {
                    "features": {
                        "type": "array",
                        "items": {"$ref": "#/$defs/feature_schemas"}
                    }
                }
            }
        }
    }
    if id_:
        schema["$id"] = id_
    return schema
