import re
from urllib.parse import urlparse

import pandas as pd
from shapely.validation import explain_validity

from .types import PYTHON_TYPES, is_numerical_type, is_scalar_type

REGEX_EMAIL = re.compile("^[^@]+@[^@]+\\.[^@]+$")
REGEX_UUID = re.compile("^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


def validate_column(data, rules):
    for value in data:
        isna = pd.isna(value)
        if isinstance(isna, bool) and isna:
            # Skip validation for NaN values or implement special handling if required
            continue

        dtype = rules.get("type")
        expected_pytype = PYTHON_TYPES.get(dtype)
        if expected_pytype is not None and not isinstance(value, expected_pytype):
            actualy_pytype = type(value)
            return [f"Value '{value}' is not of type {dtype}, is {actualy_pytype}"]

        if dtype == "string":
            issues = validate_string(value, rules)
        elif is_numerical_type(dtype):
            issues = validate_numerical(value, rules)
        elif dtype == "array":
            issues = validate_array(value, rules)
        elif dtype == "geometry":
            issues = validate_geometry(value, rules)
        elif dtype == "bounding-box":
            issues = validate_bbox(value, rules)
        elif dtype == "object":
            issues = validate_object(value, rules)
        else:
            continue

        if len(issues) > 0:
            return issues

    return []


# Geometry validation
def validate_bbox(value, rules):
    issues = []

    if value["xmin"] > value["xmax"]:
        issues.append(
            f"Bounding box has xmin value greater than xmax value: {value['xmin']} > {value['xmax']}"
        )
    elif value["ymin"] > value["ymax"]:
        issues.append(
            f"Bounding box has ymin value greater than ymax value: {value['ymin']} > {value['ymax']}"
        )

    return issues


# Geometry validation
def validate_geometry(value, rules):
    issues = []

    geom_types = rules.get("geometryTypes", [])
    if len(geom_types) > 0 and value.geom_type not in geom_types:
        allowed = ", ".join(geom_types)
        issues.append(
            f"Geometry type '{value.geom_type}' is not one of the allowed types: {allowed}"
        )

    why = explain_validity(value)
    if why != "Valid Geometry":
        issues.append(f"Geometry {value} is not valid: {why}")

    return issues


# String validation
def validate_string(value, rules):
    issues = []
    if "minLength" in rules and len(value) < rules["minLength"]:
        issues.append(
            f"String '{value}' is shorter than the minimum length of {rules['minLength']}."
        )
    if "maxLength" in rules and len(value) > rules["maxLength"]:
        issues.append(
            f"String '{value}' is longer than the maximum length of {rules['maxLength']}."
        )
    if "pattern" in rules and not re.match(rules["pattern"], value):
        issues.append(f"String '{value}' does not match the required pattern: {rules['pattern']}.")
    if "enum" in rules and value not in rules["enum"]:
        allowed = ", ".join(rules["enum"])
        issues.append(
            f"String '{value}' is not one of the allowed values in the enumeration: {allowed}"
        )
    if "format" in rules:
        if rules["format"] == "email" and not REGEX_EMAIL.match(value):
            issues.append(f"String '{value}' is not a valid email address.")
        if rules["format"] == "uri" and not urlparse(value).scheme:
            issues.append(f"String '{value}' is not a valid URI.")
        if rules["format"] == "uuid" and not REGEX_UUID.match(value):
            issues.append(f"String '{value}' is not a valid UUID.")
    return issues


# Numerical validation
def validate_numerical(value, rules):
    issues = []
    if "minimum" in rules and value < rules["minimum"]:
        issues.append(
            f"Value {value} is less than the minimum allowed value of {rules['minimum']}."
        )
    if "maximum" in rules and value > rules["maximum"]:
        issues.append(
            f"Value {value} is greater than the maximum allowed value of {rules['maximum']}."
        )
    if "exclusiveMinimum" in rules and value <= rules["exclusiveMinimum"]:
        issues.append(
            f"Value {value} is less than or equal to the exclusive minimum value of {rules['exclusiveMinimum']}."
        )
    if "exclusiveMaximum" in rules and value >= rules["exclusiveMaximum"]:
        issues.append(
            f"Value {value} is greater than or equal to the exclusive maximum value of {rules['exclusiveMaximum']}."
        )
    if "enum" in rules and value not in rules["enum"]:
        allowed = ", ".join(map(str, rules["enum"]))
        issues.append(
            f"Integer '{value}' is not one of the allowed values in the enumeration: {allowed}"
        )
    return issues


# Array validation
def validate_array(values, rules):
    issues = []

    item_schema = rules.get("items", {})

    if "minItems" in rules and len(values) < rules["minItems"]:
        issues.append(f"Array has fewer items than the minimum of {rules['minItems']}.")
    if "maxItems" in rules and len(values) > rules["maxItems"]:
        issues.append(f"Array has more items than the maximum of {rules['maxItems']}.")

    if "uniqueItems" in rules and rules["uniqueItems"]:
        item_dtype = item_schema.get("type")
        if is_scalar_type(item_dtype) and len(values) != len(set(values)):
            issues.append("Array items are not unique.")
        else:
            pass  # not supported for non-scalar types

    # todo: Further validation for 'items' if necessary
    return issues


# Object validation
def validate_object(value, rules):
    issues = []

    if "minProperties" in rules and len(value) < rules["minProperties"]:
        issues.append(f"Object has fewer properties than the minimum of {rules['minProperties']}.")
    if "maxProperties" in rules and len(value) > rules["maxProperties"]:
        issues.append(f"Object has more properties than the maximum of {rules['maxProperties']}.")

    props = rules.get("properties", {})
    # todo:
    # other_props = rules.get("additionalProperties", False)
    # pattern_props = rules.get("patternProperties", {})
    for key, val in props.items():
        if key not in value:
            issues.append(f"Key '{key}' is missing from the object.")
        # todo: Further validation based on the type of property

    return issues
