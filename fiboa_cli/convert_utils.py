from .const import STAC_TABLE_EXTENSION
from .version import fiboa_version
from .util import log, get_fs, name_from_uri, to_iso8601
from .parquet import create_parquet

from fsspec.implementations.local import LocalFileSystem
from tempfile import TemporaryDirectory
from shapely.geometry import box

import os
import re
import json
import geopandas as gpd
import pandas as pd
import sys
import zipfile
import py7zr
import flatdict
import rarfile


def convert(
        output_file, cache_path,
        urls, columns,
        id, title, description,
        input_files = None,
        bbox = None,
        providers = [],
        source_coop_url = None,
        extensions = [],
        missing_schemas = {},
        column_additions = {},
        column_filters = {},
        column_migrations = {},
        migration = None,
        file_migration = None,
        layer_filter = None,
        attribution = None,
        store_collection = False,
        license = None,
        compression = None,
        geoparquet1 = False,
        original_geometries = False,
        index_as_id = False,
        **kwargs):
    """
    Converts a field boundary datasets to fiboa.
    """
    if bbox is not None and len(bbox) != 4:
        raise ValueError("If provided, the bounding box must consist of 4 numbers")

    # Create output folder if it doesn't exist
    dir = os.path.dirname(output_file)
    if dir:
        os.makedirs(dir, exist_ok=True)

    if input_files is not None and isinstance(input_files, dict) and len(input_files) > 0:
        log("Using user provided input file(s) instead of the pre-defined file(s)", "warning")
        urls = input_files
    elif urls is None:
        raise ValueError("No input files provided")

    log("Getting file(s) if not cached yet")
    paths = download_files(urls, cache_path)

    gdfs = []
    for path, uri in paths:
        log(f"Reading {path} into GeoDataFrame(s)")
        is_parquet = path.endswith(".parquet") or path.endswith(".geoparquet")
        is_json = path.endswith(".json") or path.endswith(".geojson")
        layers = [None]
        # Parquet doesn't support layers
        if not is_parquet:
            all_layers = gpd.list_layers(path)
            if layer_filter is not None:
                layers = [layer for layer in all_layers["name"] if layer_filter(str(layer), path)]
                if len(layers) == 0:
                    log(f"No layers left for layering after filtering", "warning")

        for layer in layers:
            if layer is not None:
                kwargs["layer"] = layer
                log(f"- Reading layer {layer} into GeoDataFrame")

            if is_parquet:
                data = gpd.read_parquet(path, **kwargs)
            elif is_json:
                data = read_geojson(path, **kwargs)
            else:
                try:
                    data = gpd.read_file(path, **kwargs)
                except IndexError as e:
                    # Error may occur due to paged reading of APIs, e.g. in the LV converter
                    if str(e).startswith("index 0 is out of bounds") and len(paths) > 1:
                        log(f"read 0 features from {path}", "warning")
                        continue
                    else:
                        raise

            # 0. Run migration per file/layer
            if callable(file_migration):
                log("Applying per-file/layer migrations")
                data = file_migration(data, path, uri, layer)
                if not isinstance(data, gpd.GeoDataFrame):
                    raise ValueError("Per-file/layer migration function must return a GeoDataFrame")

            gdfs.append(data)

    gdf = pd.concat(gdfs)
    del gdfs

    log("GeoDataFrame created from source(s):")
    # Make it so that everything is shown, don't output ... if there are too many columns or rows
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    print(gdf.head())

    if index_as_id:
        gdf["id"] = gdf.index

    # 1. Run global migration
    has_migration = callable(migration)
    if has_migration:
        log("Applying global migrations")
        gdf = migration(gdf)
        if not isinstance(gdf, gpd.GeoDataFrame):
            raise ValueError("Migration function must return a GeoDataFrame")

    # 2. Run filters to remove rows that shall not be in the final data
    has_col_filters = len(column_filters) > 0
    if has_col_filters:
        log("Applying filters")
        for key, fn in column_filters.items():
            if key in gdf.columns:
                result = fn(gdf[key])
                # If the result is a tuple, the second value is a flag to potentially invert the mask
                if isinstance(result, tuple):
                    if (result[1]):
                        # Invert mask
                        mask = ~result[0]
                    else:
                        # Use mask as is
                        mask = result[0]
                else:
                    # Just got a mask, proceed
                    mask = result

                # Filter columns based on the mask
                gdf = gdf[mask]
            else:
                log(f"Column '{key}' not found in dataset, skipping filter", "warning")

    # 3. Add constant columns
    has_col_additions = len(column_additions) > 0
    if has_col_additions:
        log("Adding columns")
        for key, value in column_additions.items():
            gdf[key] = value
            columns[key] = key

    # 4. Run column migrations
    has_col_migrations = len(column_migrations) > 0
    if has_col_migrations:
        log("Applying column migrations")
        for key, fn in column_migrations.items():
            if key in gdf.columns:
                gdf[key] = fn(gdf[key])
            else:
                log(f"Column '{key}' not found in dataset, skipping migration", "warning")

    # 4b. For geometry column, fix geometries
    if not original_geometries:
        gdf.geometry = gdf.geometry.make_valid()
        gdf = gdf.explode()

    if has_migration or has_col_migrations or has_col_filters or has_col_additions:
        log("GeoDataFrame after migrations and filters:")
        print(gdf.head())

    # 5. Duplicate columns if needed
    actual_columns = {}
    for old_key, new_key in columns.items():
        if old_key in gdf.columns:
            # If the new keys are a list, duplicate the column
            if isinstance(new_key, list):
                for key in new_key:
                    gdf[key] = gdf.loc[:, old_key]
                    actual_columns[key] = key
            # If the new key is a string, plan to rename the column
            elif old_key in gdf.columns:
                actual_columns[old_key] = new_key
        # If old key is not found, remove from the schema and warn
        else:
            log(f"Column '{old_key}' not found in dataset, removing from schema", "warning")

    # 6. Rename columns
    gdf.rename(columns = actual_columns, inplace = True)

    # 7. Remove all columns that are not listed
    drop_columns = list(set(gdf.columns) - set(actual_columns.values()))
    gdf.drop(columns = drop_columns, inplace = True)

    log("GeoDataFrame fully migrated:")
    print(gdf.head())

    collection = create_collection(
        gdf,
        id, title, description, bbox,
        providers = providers,
        source_coop_url = source_coop_url,
        extensions = extensions,
        attribution = attribution,
        license = license
    )

    log("Creating GeoParquet file: " + output_file)
    config = {
        "fiboa_version": fiboa_version,
    }
    columns = list(actual_columns.values())
    pq_fields = create_parquet(gdf, columns, collection, output_file, config, missing_schemas, compression, geoparquet1)

    if store_collection:
        external_collection = add_asset_to_collection(collection, output_file, rows = len(gdf), columns = pq_fields)
        collection_file = os.path.join(os.path.dirname(output_file), "collection.json")
        log("Creating Collection file: " + collection_file)
        with open(collection_file, "w") as f:
            json.dump(external_collection, f, indent=2)

    log("Finished", "success")


def create_collection(
        gdf,
        id, title, description, bbox = None,
        providers = [],
        source_coop_url = None,
        extensions = [],
        attribution = None,
        license = None
    ):
    """
    Creates a collection for the field boundary datasets.
    """
    if bbox is None:
        bbox = list(gpd.GeoSeries([box(*gdf.total_bounds)], crs=gdf.crs).to_crs(epsg=4326).total_bounds)

    collection = {
        "fiboa_version": fiboa_version,
        "fiboa_extensions": extensions,
        "type": "Collection",
        "id": id.strip(),
        "title": title.strip(),
        "description": description.strip(),
        "license": "proprietary",
        "providers": providers,
        "extent": {
            "spatial": {
                "bbox": [bbox]
            },
        },
        "links": []
    }

    if "determination_datetime" in gdf.columns:
        dates = pd.to_datetime(gdf['determination_datetime'])
        min_time = to_iso8601(dates.min())
        max_time = to_iso8601(dates.max())

        collection["extent"]["temporal"] = {
            "interval": [[min_time, max_time]]
        }
        # Without temporal extent it's not valid STAC
        collection["stac_version"] = "1.0.0"

    # Add fiboa CLI to providers
    collection["providers"].append({
        "name": "fiboa CLI",
        "roles": ["processor"],
        "url": "https://pypi.org/project/fiboa-cli"
    })

    # Add source coop to providers if applicable
    if source_coop_url is not None:
        collection["providers"].append({
            "name": "Source Cooperative",
            "roles": ["host"],
            "url": source_coop_url
        })

    # Update attribution
    if attribution is not None:
        collection["attribution"] = attribution

    # Update license
    if isinstance(license, dict):
        collection["links"].append(license)
    elif isinstance(license, str):
        if license.lower() == "dl-de/by-2-0":
            collection["links"].append({
                "href": "https://www.govdata.de/dl-de/by-2-0",
                "title": "Data licence Germany - attribution - Version 2.0",
                "type": "text/html",
                "rel": "license"
            })
        elif license.lower() == "dl-de/zero-2-0":
            collection["links"].append({
                "href": "https://www.govdata.de/dl-de/zero-2-0",
                "title": "Data licence Germany - Zero - Version 2.0",
                "type": "text/html",
                "rel": "license"
            })
        elif re.match(r"^[\w\.-]+$", license):
            collection["license"] = license
        else:
            log(f"Invalid license identifier: {license}", "warning")
    else:
        log(f"License information missing", "warning")

    return collection


def add_asset_to_collection(collection, output_file, rows = None, columns = None):
    c = collection.copy()
    if "assets" not in c or not isinstance(c["assets"], dict):
        c["assets"] = {}
    if "stac_extensions" not in c or not isinstance(c["stac_extensions"], list):
        c["stac_extensions"] = []

    c["stac_extensions"].append(STAC_TABLE_EXTENSION)

    table_columns = []
    for column in columns:
        table_columns.append({
            "name": column.name,
            "type": str(column.type)
        })

    asset = {
        "href": os.path.basename(output_file),
        "title": "Field Boundaries",
        "type": "application/vnd.apache.parquet",
        "roles": [
            "data"
        ],
        "table:columns": table_columns,
        "table:primary_geometry": "geometry"
    }
    if rows is not None:
        asset["table:row_count"] = rows

    c["assets"]["data"] = asset

    return c


def download_files(uris, cache_folder = None):
    """Download (and cache) files from various sources"""
    if cache_folder is None:
        args = {}
        if sys.version_info.major >= 3 and sys.version_info.minor >= 12:
            args["delete"] = False # only available in Python 3.12 and later
        with TemporaryDirectory(**args) as tmp_folder:
            cache_folder = tmp_folder

    if isinstance(uris, str):
        uris = {uris: name_from_uri(uris)}

    paths = []
    i = 0
    for uri, target in uris.items():
        i = i + 1
        is_archive = isinstance(target, list)
        if is_archive:
            try:
                name = name_from_uri(uri)
                # if there's no file extension, it's likely a folder, which may not be unique
                if "." not in name:
                    name = str(i)
            except:
                name = str(i)
        else:
            name = target

        source_fs = get_fs(uri)
        cache_fs = get_fs(cache_folder)
        if not cache_fs.exists(cache_folder):
            cache_fs.makedirs(cache_folder)

        if isinstance(source_fs, LocalFileSystem):
            cache_file = uri
        else:
            cache_file = os.path.join(cache_folder, name)

        zip_folder = os.path.join(cache_folder, "extracted." + os.path.splitext(name)[0])
        must_extract = is_archive and not os.path.exists(zip_folder)

        if (not is_archive or must_extract) and not cache_fs.exists(cache_file):
            with cache_fs.open(cache_file, mode='wb') as file:
                stream_file(source_fs, uri, file)

        if must_extract:
            if zipfile.is_zipfile(cache_file):
                try:
                    with zipfile.ZipFile(cache_file, 'r') as zip_file:
                        zip_file.extractall(zip_folder)
                except NotImplementedError as e:
                    if str(e) != "That compression method is not supported":
                        raise
                    import zipfile_deflate64
                    with zipfile_deflate64.ZipFile(cache_file, 'r') as zip_file:
                        zip_file.extractall(zip_folder)
            elif py7zr.is_7zfile(cache_file):
                with py7zr.SevenZipFile(cache_file, 'r') as sz_file:
                    sz_file.extractall(zip_folder)
            elif name.endswith(".rar"):
                with rarfile.RarFile(cache_file, 'r') as w:
                    w.extractall(zip_folder)
            else:
                raise ValueError("Only ZIP and 7Z files are supported for extraction")

        if is_archive:
            for filename in target:
                paths.append((os.path.join(zip_folder, filename), uri))
        else:
            paths.append((cache_file, uri))

    return paths


def stream_file(fs, src_uri, dst_file, chunk_size = 10 * 1024 * 1024):
    with fs.open(src_uri, mode='rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            dst_file.write(chunk)


def normalize_geojson_properties(feature):
    # Convert properties of type dict to dot notation
    feature["properties"] = flatdict.FlatDict(feature["properties"], delimiter=".")

    # Preserve id: https://github.com/geopandas/geopandas/issues/1208
    if "id" not in feature["properties"]:
        feature["properties"]["id"] = feature["id"]

    return feature


def read_geojson(path, **kwargs):
    with open(path, **kwargs) as f:
        obj = json.load(f)

    if not isinstance(obj, dict):
        raise ValueError("JSON file must contain a GeoJSON object")
    elif obj["type"] != "FeatureCollection":
        raise ValueError("JSON file must contain a GeoJSON FeatureCollection")

    obj["features"] = list(map(normalize_geojson_properties, obj["features"]))

    return gpd.GeoDataFrame.from_features(obj, crs = "EPSG:4326")
