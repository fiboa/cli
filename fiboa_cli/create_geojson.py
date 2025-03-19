import json
import os

import numpy as np
import pandas as pd

from .util import load_parquet_data, load_parquet_schema, log, parse_metadata, to_iso8601


def create_geojson(file, out, split=False, num=None, indent=None):
    dir = os.path.dirname(out)
    if dir:
        os.makedirs(dir, exist_ok=True)

    schema = load_parquet_schema(file)
    collection = parse_metadata(schema, b"fiboa")
    geodata = load_parquet_data(file, nrows=num)
    geodata = geodata.to_crs(epsg=4326)

    if num is None:
        count = len(geodata)
        log(f"Found {count} features...")

    # todo: we shouldn't use iterfeature / __geo_interface__ directly
    # it doesn't correctly coverts some data types which are present in the fiboa schema
    # e.g. lists of tuples into a dict
    if split:
        if collection is not None:
            collection_name = "collection.json"
            collection_path = os.path.join(out, collection_name)
            write_json(collection, collection_path, indent)

        i = 1
        for obj in geodata.iterfeatures():
            if (i % 1000) == 0:
                log(f"{i}...", nl=(i % 10000) == 0)

            obj = fix_geojson(obj)

            if collection is not None:
                links = obj.get("links", [])
                links.append(
                    {"href": collection_name, "rel": "collection", "type": "application/json"}
                )
                obj["links"] = links

            id = obj.get("id", i)
            path = os.path.join(out, f"{id}.json")
            write_json(obj, path, indent)

            i += 1

    else:
        obj = geodata.__geo_interface__
        del obj["bbox"]
        obj["features"] = list(map(fix_geojson, obj["features"]))
        obj["fiboa"] = collection
        if os.path.isdir(out):
            out = os.path.join(out, "features.json")
        write_json(obj, out, indent)


def write_json(obj, path, indent=None):
    with open(path, "w") as f:
        json.dump(obj, f, allow_nan=False, indent=indent, cls=FiboaJSONEncoder)


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

    return obj


class FiboaJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, pd.Timestamp):
            return to_iso8601(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super().default(obj)
