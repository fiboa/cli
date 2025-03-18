# TEMPLATE FOR A FIBOA CONVERTER
#
# Copy this file and rename it to something sensible.
# The name of the file will be the name of the converter in the cli.
# If you name it 'de_abc' you'll be able to run `fiboa convert de_abc` in the cli.

from ..convert_utils import convert as convert_

import re
import pandas as pd

# File to read the data from
# Can read any tabular data format that GeoPandas can read through read_file()
# Supported protcols: HTTP(S), GCS, S3, or the local file system

# original data source : https://data.public.lu/en/datasets/referentiel-des-parcelles-flik/#resources
SOURCES = "/mnt/c/Snehal/Kerner Lab/tge-fiboa/luxembourg/all_parcels.gpkg"  # data subset for FieldScapes

# Unique identifier for the collection
ID = "fieldscapes_luxembourg_2022"
# Title of the collection
TITLE = "Field boundaries for Luxembourg (FieldScapes)"
# Description of the collection. Can be multiline and include CommonMark.
# Adapted from https://collections.eurodatacube.com/luxembourg-lpis/readme.html
DESCRIPTION = """Luxembourg's Land Parcel Identification System (LPIS) is managed by The Administration of Technical Agricultural Services (ASTA). The data is made available to the public on The Luxembourg Data Platform based on the Creative Commons 1.0 Universal (CC0 1.0) Public Domain Dedication.The plot-based parcel reference system (FLIK) in Luxembourg was digitally recorded for the first time in 2005 based on aerial photos. Since then, the system has been continuously revised via the latest aerial images.Onsite measurements using GPS are carried out for unclear boundaries cases as well an assessment of the parcel's eligibility for payment.The FLIK parcels are categorized into eligible agricultural parcels, eligible vineyard parcels, ineligible parcels, and non-payable objects. The data has been uploaded to geoDB and is available from 2016 to 2021 annually with updates expected annually."""
# Bounding box of the data in WGS84 coordinates
BBOX = [5.916329, 6.331939, 49.526297 , 49.957896]

# Provider name, can be None if not applicable, must be provided if PROVIDER_URL is provided
PROVIDER_NAME = "Agricultural Technical Services Administration (ASTA)"
# URL to the homepage of the data or the provider, can be None if not applicable
PROVIDER_URL = "https://data.public.lu/en/datasets/referentiel-des-parcelles-flik/#resourcese"
# Attribution, can be None if not applicable 
ATTRIBUTION = " Administration des services techniques de l'agriculture - Service SIG"


# License of the data, either
# 1. a SPDX license identifier (including "dl-de/by-2-0" / "dl-de/zero-2-0"), or
LICENSE = "CC0-1.0"
# 2. a STAC Link Object with relation type "license"
# LICENSE = {"title": "CC-BY-4.0", "href": "https://creativecommons.org/licenses/by/4.0/", "type": "text/html", "rel": "license"}

# Map original column names to fiboa property names
# You also need to list any column that you may have added in the MIGRATION function (see below).
COLUMNS = {
    'FLIK' : 'id', # fiboa core field
    'CODE_ELEM' : 'category', #fiboa custom field
    'CODE_COM' : 'commune_code', #fiboa custom field
    'CODE_SECT' : 'section_code', #fiboa custom field
    'SURFACE' : 'area', # fiboa core field
    'PERIMETRE':'perimeter', #fiboa custom field
    'geometry':'geometry'# fiboa core field
}

# Add columns with constant values.
# The key is the column name, the value is a constant value that's used for all rows.
ADD_COLUMNS = {
    "determination_datetime": "2022-12-31T00:00:00Z"  # fiboa core field
}

# A list of implemented extension identifiers
EXTENSIONS = []

# Functions to migrate data in columns to match the fiboa specification.
# Example: You have a column area_m in square meters and want to convert
# to hectares as required for the area field in fiboa.
# Function signature:
#   func(column: pd.Series) -> pd.Series
COLUMN_MIGRATIONS = {
    'SURFACE': lambda column: column * 0.0001,
    'CODE_ELEM': lambda column: column.map({'P': 'Agricultural Parcel', 'V': 'Vineyard parcel', 'D': 'Ineligible parcel', 'N':'Non-payable objects'}),
}

# Filter columns to only include the ones that are relevant for the collection,
# e.g. only rows that contain the word "agriculture" but not "forest" in the column "land_cover_type".
# Lamda function accepts a Pandas Series and returns a Series or a Tuple with a Series and True to inverse the mask.
COLUMN_FILTERS = {
    'CODE_ELEM': lambda col: (col.isin(["Agricultural Parcel"]), True)
}

# Custom function to migrate the GeoDataFrame if the other options are not sufficient
# This should be the last resort!
# Function signature:
#   func(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame
MIGRATION = None


# Custom function to execute actions on the the GeoDataFrame that are loaded from individual file.
# This is useful if the data is split into multiple files and columns should be added or changed
# on a per-file basis for example.
# The path contains the local path to the file that was read.
# The uri contains the URL that was read.
# Function signature:
#   func(gdf: gpd.GeoDataFrame, path: string, uri: string) -> gpd.GeoDataFrame
FILE_MIGRATION = None



# Schemas for the fields that are not defined in fiboa
# Keys must be the values from the COLUMNS dict, not the keys
MISSING_SCHEMAS = {
    'properties': {
        'category': {
            'type': 'string',
            'enum' : ['Agricultural Parcel', 'Vineyard parcel', 'Ineligible parcel', 'Non-payable objects']
        },
        'commune_code': {
            'type': 'string'
        },
        'section_code': {
            'type': 'string'
        },
        'perimeter': {
            'type': 'float',
            'exclusiveMinimum': 0
        },
    }
}


# Conversion function, usually no changes required
def convert(output_file, input_files = None, cache = None, source_coop_url = None, collection = False, compression = None):
    """
    Converts the field boundary datasets to fiboa.

    For reference, this is the order in which the conversion steps are applied:
    0. Read GeoDataFrame from file(s) and run the FILE_MIGRATION function if provided
    1. Run global migration (if provided through MIGRATION)
    2. Run filters to remove rows that shall not be in the final data
       (if provided through COLUMN_FILTERS)
    3. Add columns with constant values
    4. Run column migrations (if provided through COLUMN_MIGRATIONS)
    5. Duplicate columns (if an array is provided as the value in COLUMNS)
    6. Rename columns (as provided in COLUMNS)
    7. Remove columns (if column is not present as value in COLUMNS)
    8. Create the collection
    9. Change data types of the columns based on the provided schemas
    (fiboa spec, extensions, and MISSING_SCHEMAS)
    10. Write the data to the Parquet file

    Parameters:
    output_file (str): Path where the Parquet file shall be stored.
    cache (str): Path to a cached folder for the data. Default: None.
                      Can be used to avoid repetitive downloads from the original data source.
    source_coop_url (str): URL to the (future) Source Cooperative repository. Default: None
    collection (bool): Additionally, store the collection separate from Parquet file. Default: False
    compression (str): Compression method for the Parquet file. Default: zstd
    kwargs: Additional keyword arguments for GeoPanda's read_file() or read_parquet() function.
    """
    convert_(
        output_file,
        cache,
        SOURCES,
        COLUMNS,
        ID,
        TITLE,
        DESCRIPTION,
        bbox = BBOX,
        input_files=input_files,
        provider_name=PROVIDER_NAME,
        provider_url=PROVIDER_URL,
        source_coop_url=source_coop_url,
        extensions=EXTENSIONS,
        missing_schemas=MISSING_SCHEMAS,
        column_additions=ADD_COLUMNS,
        column_migrations=COLUMN_MIGRATIONS,
        column_filters=COLUMN_FILTERS,
        migration=MIGRATION,
        file_migration=FILE_MIGRATION,
        attribution=ATTRIBUTION,
        store_collection=collection,
        license=LICENSE,
        compression=compression,
    )
