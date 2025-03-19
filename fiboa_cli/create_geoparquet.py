import os

from .parquet import create_parquet
from .util import get_collection, load_file, log


def create_geoparquet(config):
    output_file = config.get("out")

    # Load all features from the GeoJSON files
    features = []
    geojson = {}
    file = None
    files = config.get("files")
    for file in files:
        geojson = load_file(file)
        if geojson["type"] == "Feature":
            features.append(geojson)
        elif geojson["type"] == "FeatureCollection":
            features += geojson["features"]
        else:
            log(f"{file}: Skipped - Unsupported GeoJSON type, must be Feature or FeatureCollection")

    if len(features) == 0:
        raise Exception("No valid features provided as input files")

    # Add a STAC collection to the fiboa property to the Parquet metadata
    # Note: for features this loads the collection of the last feature only
    # if not provided specifically via collection parameter
    collection = get_collection(geojson, config.get("collection"), file)

    if collection is None:
        # No collection found, create a default collection based on parameters
        version = config.get("fiboa_version")
        collection = {
            "fiboa_version": version,
            "fiboa_extensions": list(config.get("extension_schemas", {}).keys()),
        }

    # add a default id based on the output filename
    if "id" not in collection or not collection["id"]:
        collection["id"] = os.path.basename(output_file)

    # Make the fiboa_version consistent with the collection
    if "fiboa_version" in collection:
        config["fiboa_version"] = collection["fiboa_version"]

    # Get a list of the properties/columns (without duplicates)
    columns = set(["id", "geometry"])
    for feature in features:
        keys = feature["properties"].keys()
        columns.update(keys)

    columns = list(columns)
    columns.sort()

    # Create the Parquet file
    create_parquet(features, columns, collection, output_file, config)
    log(f"Wrote to {output_file}", "success")
