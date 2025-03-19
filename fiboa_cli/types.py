import datetime

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.types as pat
from shapely.geometry.base import BaseGeometry


def is_enum(schema):
    return isinstance(schema.get("enum"), list)


def is_integer_type(dtype):
    return dtype.startswith("int") or dtype.startswith("uint")


def is_floating_type(dtype):
    return dtype == "float" or dtype == "double"


def is_numerical_type(dtype):
    return is_integer_type(dtype) or is_floating_type(dtype)


def is_temporal_type(dtype):
    return dtype == "date" or dtype == "date-time"


def is_scalar_type(dtype):
    return (
        dtype == "string"
        or dtype == "binary"
        or dtype == "boolean"
        or is_numerical_type(dtype)
        or is_temporal_type(dtype)
    )


def get_geopandas_dtype(type, required=False, schema={}, return_category=False):
    """
    fiboa datatypes to geopandas datatypes
    """
    if return_category and is_enum(schema) and (type == "string" or is_integer_type(type)):
        return "category"
    elif type == "boolean":
        if required:
            return "bool"
        else:
            return "boolean"
    elif type == "int8":
        if required:
            return "int8"
        else:
            return "Int8"
    elif type == "uint8":
        if required:
            return "uint8"
        else:
            return "UInt8"
    elif type == "int16":
        if required:
            return "int16"
        else:
            return "Int16"
    elif type == "uint16":
        if required:
            return "uint16"
        else:
            return "UInt16"
    elif type == "int32":
        if required:
            return "int32"
        else:
            return "Int32"
    elif type == "uint32":
        if required:
            return "uint32"
        else:
            return "UInt32"
    elif type == "int64":
        if required:
            return "int64"
        else:
            return "Int64"
    elif type == "uint64":
        if required:
            return "uint64"
        else:
            return "UInt64"
    elif type == "float":
        if required:
            return "float32"
        else:
            return "Float32"
    elif type == "double":
        if required:
            return "float64"
        else:
            return "Float64"
    elif type == "binary":
        return "bytearray"  # todo: check
    elif type == "string":
        if required:
            return "str"
        else:
            return "string"
    elif type == "array":
        return lambda series: series.apply(lambda x: np.array(x))
    elif type == "object":
        return "object"
    elif type == "date" or type == "date-time":
        return lambda series: pd.to_datetime(series)
    elif type == "geometry":
        return (None,)  # not a column, don't convert geometry
    elif type == "bounding-box":
        return "object"
    else:
        return None


def get_pyarrow_field(name, pa_type=None, schema=None, required=False):
    if pa_type is None:
        pa_type = get_pyarrow_type(schema)
    if pa_type is None:
        return None
    else:
        return pa.field(name, pa_type, nullable=not required)


def get_pyarrow_type(schema):
    """
    fiboa datatypes to pyarrow datatypes
    """
    dtype = schema.get("type")
    if dtype == "boolean":
        return pa.bool_()
    elif is_integer_type(dtype) or dtype == "string" or dtype == "binary":
        return getattr(pa, dtype)()
    elif dtype == "float":
        return pa.float32()
    elif dtype == "double":
        return pa.float64()
    elif dtype == "array":
        pa_subtype = get_pyarrow_type(schema.get("items", {}))
        return pa.list_(pa_subtype)
    elif dtype == "object":
        pattern_properties = schema.get("patternProperties", {})
        additonal_properties = schema.get("additionalProperties", False)
        if additonal_properties is True:
            raise Exception("Additional properties for objects are not supported")
        elif len(pattern_properties) > 0:
            if len(pattern_properties) > 1:
                raise Exception("Multiple pattern properties are not supported")
            _, subschema = pattern_properties.popitem()
            values = get_pyarrow_type(subschema)
            return pa.map_(pa.string(), values)
        else:
            properties = schema.get("properties", {})
            required_props = schema.get("required", [])
            fields = []
            for name, schema in properties.items():
                field = get_pyarrow_field(name, schema=schema, required=name in required_props)
                fields.append(field)
            return pa.struct(fields)
    elif dtype == "date":
        return pa.date32()
    elif dtype == "date-time":
        return pa.timestamp("ms", tz="UTC")
    elif dtype == "geometry":
        return pa.binary()
    elif dtype == "bounding-box":
        coord_schema = {"type": "float"}
        return pa.struct(
            [
                get_pyarrow_field("xmin", schema=coord_schema, required=True),
                get_pyarrow_field("ymin", schema=coord_schema, required=True),
                get_pyarrow_field("xmax", schema=coord_schema, required=True),
                get_pyarrow_field("ymax", schema=coord_schema, required=True),
            ]
        )
    else:
        return None


def get_pyarrow_type_for_geopandas(dtype):
    """
    geopandas datatypes to pyarrow datatypes
    """
    dtype = dtype.lower()
    if dtype == "bool":
        return pa.bool_()
    elif dtype == "string" or dtype == "|s0" or dtype == "<u0":
        return pa.string()
    elif (
        dtype == "float128"
        or dtype == "record"
        or dtype == "timedelta64"
        or dtype.startswith("complex")
    ):  # complex128/256/512
        raise Exception(f"Unsupported data type: {dtype}")
    elif (
        dtype.startswith("int") or dtype.startswith("uint") or dtype.startswith("float")
    ):  # float16/32/64
        return getattr(pa, dtype)()
    elif dtype == "object":
        return pa.string()  # todo
    elif dtype == "datetime64":
        return pa.timestamp("ms", tz="UTC")
    else:
        return None


# checks pyarrow datatypes
PA_TYPE_CHECK = {
    "boolean": pat.is_boolean,
    "int8": pat.is_int8,
    "uint8": pat.is_uint8,
    "int16": pat.is_int16,
    "uint16": pat.is_uint16,
    "int32": pat.is_int32,
    "uint32": pat.is_uint32,
    "int64": pat.is_int64,
    "uint64": pat.is_uint64,
    "float": pat.is_float32,
    "double": pat.is_float64,
    "binary": pat.is_binary,
    "string": pat.is_string,
    "array": pat.is_list,
    "object": lambda x: pat.is_struct(x) or pat.is_map(x),
    "date": pat.is_date32,
    "date-time": pat.is_timestamp,
    "geometry": pat.is_binary,
    "bounding-box": pat.is_struct,
}


# checks pyarrow datatypes
PYTHON_TYPES = {
    "boolean": (bool, np.bool_),
    "int8": (int, np.int8),
    "uint8": (int, np.uint8),
    "int16": (int, np.int16),
    "uint16": (int, np.uint16),
    "int32": (int, np.int32),
    "uint32": (int, np.uint32),
    "int64": (int, np.int64),
    "uint64": (int, np.uint64),
    "float": (float, np.float32),
    "double": (float, np.float64),
    "binary": (str, np.bytes_),
    "string": (str, np.str_),
    "array": (list, np.ndarray),
    "object": dict,
    "date": (datetime.date, np.datetime64),
    "date-time": (datetime.datetime, np.datetime64),
    "geometry": BaseGeometry,
    "bounding-box": dict,
}

LOG_STATUS_COLOR = {"info": "white", "warning": "yellow", "error": "red", "success": "green"}

SUPPORTED_PROTOCOLS = ["http", "https", "s3", "gs"]
