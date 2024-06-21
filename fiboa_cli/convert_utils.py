from .const import STAC_TABLE_EXTENSION
from .version import fiboa_version
from .util import log, get_fs, name_from_uri, to_iso8601
from .parquet import create_parquet

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

def convert(
        output_file, cache_path,
        urls, columns,
        id, title, description,
        input_files = None,
        bbox = None,
        provider_name = None,
        provider_url = None,
        source_coop_url = None,
        extensions = [],
        missing_schemas = {},
        column_additions = {},
        column_filters = {},
        column_migrations = {},
        migration = None,
        file_migration = None,
        attribution = None,
        store_collection = False,
        license = None,
        compression = None,
        explode_multipolygon = False,
        **kwargs):
    """
    Converts a field boundary datasets to fiboa.
    """
    if bbox is not None and len(bbox) != 4:
        raise ValueError("If provided, the bounding box must consist of 4 numbers")

    if input_files is not None and isinstance(input_files, dict) and len(input_files) > 0:
        log("Using user provided input file(s) instead of the pre-defined file(s)", "warning")
        urls = input_files
    elif urls is None:
        raise ValueError("No input files provided")

    log("Getting file(s) if not cached yet")
    paths = download_files(urls, cache_path)

    log("Reading into GeoDataFrame")
    gdfs = []
    for path, uri in paths:
        # If file is a parquet file then read with read_parquet
        if path.endswith(".parquet") or path.endswith(".geoparquet"):
            data = gpd.read_parquet(path, **kwargs)
        else:
            data = gpd.read_file(path, **kwargs)

        # 0. Run migration per file
        if callable(file_migration):
            log("Applying per file migrations")
            data = file_migration(data, path, uri)
            if not isinstance(data, gpd.GeoDataFrame):
                raise ValueError("Per-file migration function must return a GeoDataFrame")

        gdfs.append(data)

    gdf = pd.concat(gdfs)
    del gdfs

    log("GeoDataFrame created from source(s):")
    print(gdf.head())

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

    # 4b. For geometry column, convert multipolygon type to polygon
    if explode_multipolygon:
        gdf = gdf.explode(index_parts=False)

    if has_migration or has_col_migrations or has_col_filters or has_col_additions or explode_multipolygon:
        log("GeoDataFrame after migrations and filters:")
        print(gdf.head())

    # 5. Duplicate columns if needed
    actual_columns = {}
    for old_key, new_key in columns.items():
        # If new keys are a list, duplicate the column
        if isinstance(new_key, list):
            for key in new_key:
                gdf[key] = gdf.loc[:, old_key]
                actual_columns[key] = key
        # If new key is a string, plan to rename the column
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
        provider_name = provider_name,
        provider_url = provider_url,
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
    pq_fields = create_parquet(gdf, columns, collection, output_file, config, missing_schemas, compression)

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
        provider_name = None,
        provider_url = None,
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
        "id": id,
        "title": title,
        "description": description,
        "license": "proprietary",
        "providers": [],
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

    # Add providers
    if provider_name is not None:
        collection["providers"].append({
            "name": provider_name,
            "roles": ["producer", "licensor"],
            "url": provider_url
        })

    collection["providers"].append({
        "name": "fiboa CLI",
        "roles": ["processor"],
        "url": "https://pypi.org/project/fiboa-cli"
    })

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

        cache_fs = get_fs(cache_folder)
        if not cache_fs.exists(cache_folder):
            cache_fs.makedirs(cache_folder)

        cache_file = os.path.join(cache_folder, name)
        zip_folder = os.path.join(cache_folder, "extracted." + os.path.splitext(name)[0])
        must_extract = is_archive and not os.path.exists(zip_folder)

        if (not is_archive or must_extract) and not cache_fs.exists(cache_file):
            source_fs = get_fs(uri)
            with cache_fs.open(cache_file, mode='wb') as file:
                stream_file(source_fs, uri, file)

        if must_extract:
            if zipfile.is_zipfile(cache_file):
                with zipfile.ZipFile(cache_file, 'r') as zip_file:
                    zip_file.extractall(zip_folder)
            elif py7zr.is_7zfile(cache_file):
                with py7zr.SevenZipFile(cache_file, 'r') as sz_file:
                    sz_file.extractall(zip_folder)
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
