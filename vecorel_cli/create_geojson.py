import json
import os

import numpy as np
import pandas as pd

from .util import load_parquet_data, load_parquet_schema, log, parse_metadata, to_iso8601


def create_geojson(file, out, split=False, num=None, indent=None):
    directory = os.path.dirname(out)
    if directory:
        os.makedirs(directory, exist_ok=True)

    schema = load_parquet_schema(file)
    collection = parse_metadata(schema, b"collection")
    geodata = load_parquet_data(file, nrows=num)
    geodata = geodata.to_crs(epsg=4326)

    if num is None:
        count = len(geodata)
        log(f"Found {count} features...")

    # todo: we shouldn't use iterfeature / __geo_interface__ directly
    # it doesn't correctly coverts some data types which are present in the Vecorel SDL
    # e.g. lists of tuples into a dict
    if split:
        i = 1
        for obj in geodata.iterfeatures():
            if (i % 1000) == 0:
                log(f"{i}...", nl=(i % 10000) == 0)

            if isinstance(collection, dict):
                obj["properties"].update(collection)

            obj = fix_geojson(obj)

            id = obj.get("id", i)
            path = os.path.join(out, f"{id}.json")
            write_json(obj, path, indent)

            i += 1
    else:
        obj = geodata.__geo_interface__
        del obj["bbox"]

        obj["features"] = list(map(fix_geojson, obj["features"]))

        if isinstance(collection, dict):
            obj.update(collection)

        if os.path.isdir(out):
            out = os.path.join(out, "features.json")
        write_json(obj, out, indent)


def write_json(obj, path, indent=None):
    with open(path, "w") as f:
        json.dump(obj, f, allow_nan=False, indent=indent, cls=VecorelJSONEncoder)


def fix_geojson(obj):
    # Fix id
    if "id" in obj["properties"]:
        obj["id"] = obj["properties"]["id"]
    del obj["properties"]["id"]

    # Fix bbox
    if (
        "bbox" not in obj
        and "bbox" in obj["properties"]
        and isinstance(obj["properties"]["bbox"], dict)
    ):
        bbox = obj["properties"]["bbox"]
        obj["bbox"] = [bbox["xmin"], bbox["ymin"], bbox["xmax"], bbox["ymax"]]
        del obj["properties"]["bbox"]

    # Remove null values
    obj["properties"] = fix_omit_nulled_properties(obj["properties"])

    return obj


def fix_omit_nulled_properties(obj):
    for key in obj.keys():
        if obj[key] is None:
            del obj[key]
        elif isinstance(obj[key], dict):
            obj[key] = fix_omit_nulled_properties(obj[key])
        elif isinstance(obj[key], list):
            for i, item in enumerate(obj[key]):
                if not isinstance(item, dict):
                    continue
                obj[key][i] = fix_omit_nulled_properties(item)

    return obj


class VecorelJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, pd.Timestamp):
            return to_iso8601(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super().default(obj)
