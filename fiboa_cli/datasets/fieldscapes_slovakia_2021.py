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

# original data : https://data.slovensko.sk/datasety/7998b5ab-83f4-80f4-9ba3-7fa62dd79cd9

SOURCES = "/mnt/c/Snehal/Kerner Lab/tge-fiboa/slovakia/all_parcels.gpkg" # data subset for FieldScapes

# Unique identifier for the collection
ID = "fieldscapes_slovakia_2021"
# Title of the collection
TITLE = "Field boundaries for Slovakia (FieldScapes)"
# Description of the collection. Can be multiline and include CommonMark.
DESCRIPTION = """(LPIS parts of land blocks 2021) LPIS is an agricultural land identification system. It represents the vector boundaries of agricultural land and carries information about the unique code, acreage, culture/land use, etc., which is used as a reference for farmers' applications, for administrative and cross-checks, on-site checks and also checks using remote sensing methods.

"""
# Bounding box of the data in WGS84 coordinates
BBOX = [17.4637394591015997,22.1627790444453012,47.7436593798097988, 49.0699891361128024]


# Provider name, can be None if not applicable, must be provided if PROVIDER_URL is provided
PROVIDER_NAME = "Agricultural Payment Agency" # EU Data Citation
# URL to the homepage of the data or the provider, can be None if not applicable
PROVIDER_URL = "https://data.slovensko.sk/datasety/7998b5ab-83f4-80f4-9ba3-7fa62dd79cd"
# Attribution, can be None if not applicable
ATTRIBUTION = "None"

# License of the data, either
# 1. a SPDX license identifier (including "dl-de/by-2-0" / "dl-de/zero-2-0"), or
LICENSE = "CC0-1.0"
# 2. a STAC Link Object with relation type "license"
# LICENSE = {"title": "CC-BY-4.0", "href": "https://creativecommons.org/licenses/by/4.0/", "type": "text/html", "rel": "license"}

# Map original column names to fiboa property names
# You also need to list any column that you may have added in the MIGRATION function (see below).
COLUMNS = {
'ID_KD' : 'id', # fiboa core field
'LOKALITA' : 'municipality',
'SPOSOBILOS' : 'eligibility_for_subsidies',
'KULTURA' : 'arable_crop_class_code',
'KULTURA_CI': 'arable_crop_class_icode',
'KULTURA_NA' : 'arable_crop_class',
'Shape_Leng' : 'perimeter',
'Shape_Area' : 'area', # fiboa core field, sq. m
'geometry': 'geometry'
}

# Add columns with constant values.
# The key is the column name, the value is a constant value that's used for all rows.
ADD_COLUMNS = {
    "determination_datetime": "2021-04-09T00:00:00Z"
}

# A list of implemented extension identifiers
EXTENSIONS = []

# Functions to migrate data in columns to match the fiboa specification.
# Example: You have a column area_m in square meters and want to convert
# to hectares as required for the area field in fiboa.
# Function signature:
#   func(column: pd.Series) -> pd.Series
COLUMN_MIGRATIONS = {
    "Shape_Area": lambda column: column * 0.0001,
    'SPOSOBILOS': lambda column: column.map({'spôsobilý':'eligible', 'nespôsobilý':'ineligible'}),
    'KULTURA_NA': lambda column: column.map({'orná pôda' : 'arable land', 'vinica' : 'vineyard', 'trvalý trávny porast' : 'permanent grassland', 'ovocný sad':'orchard',
       'trvalé plodiny' : 'permanent crops', 'poľnohospodárska pôda' : 'agricultural land', 'chmelnica' : 'hops',
       'zalesnená poľnohospodárska pôda' : 'forested agricultural land'})

}


# Filter columns to only include the ones that are relevant for the collection,
# e.g. only rows that contain the word "agriculture" but not "forest" in the column "land_cover_type".
# Lamda function accepts a Pandas Series and returns a Series or a Tuple with a Series and True to inverse the mask.
COLUMN_FILTERS = {
    "KULTURA_NA": lambda col: (col.isin(["arable land", "permanent crops"]), True)
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
    "properties": {
        "municipality": {
            "type": "string"
        },
        "eligibility_for_subsidies": {
            "type": "string"
        },
        "arable_crop_class_code": {
            "type": "string"
        },
        "arable_crop_class": {
            "type": "string",
            "enum" : ['arable land', 'vineyard', 'permanent grassland', 'orchard', 'permanent crops', 'agricultural land', 'hops', 'forested agricultural land']
        },      
        "arable_crop_class_icode": {
            "type": "int8"
        }      


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
