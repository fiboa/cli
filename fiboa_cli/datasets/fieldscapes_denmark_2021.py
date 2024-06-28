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

# data original source : https://landbrugsgeodata.fvm.dk/
SOURCES = "/mnt/c/Snehal/Kerner Lab/tge-fiboa/denmark/all_parcels.gpkg" # data subset for FieldScapes

# Unique identifier for the collection
ID = "fieldscapes_denmark_2021"
# Title of the collection
TITLE = "Field boundaries for Denmark (FieldScapes)"
# Description of the collection. Can be multiline and include CommonMark.

# Description in also adapted from https://collections.eurodatacube.com/denmark-lpis/
DESCRIPTION = """Danish Land Parcel Identification System (LPIS) data collection or (field blocks/ 'Markblokke') is managed by The Danish Agency for Agriculture.

The field block map is a digital field map, with agricultural areas gathered in field blocks. A field block is a geographically coherent unit consisting of agricultural land. The boundaries of the field blocks typically follow permanent divisions in the landscape. The map is used in the administration of cases linked to the geographical determination of cultivation areas, primarily by the EU's area-based support schemes. The field block map is continuously updated on the basis of orthophotos and reports from farmers and authorities. The field block map covers approx. 2.8 million hectares of agricultural land. Each field block is identified with a field block number, area, type. A field block means a continuous area on which one or more farmers grow one or more different crops. The map is updated every night with changes from case processing."""
# Bounding box of the data in WGS84 coordinates
BBOX = [8.7378109937414692,10.4170362955184004, 55.1917137800704012, 57.4329738730357988]

# Provider name, can be None if not applicable, must be provided if PROVIDER_URL is provided
PROVIDER_NAME = "The Danish Agency for Agriculture"
# URL to the homepage of the data or the provider, can be None if not applicable
PROVIDER_URL = "https://geodata-info.dk/srv/eng/catalog.search#/metadata/d91b2c99-d9b0-4e6d-b323-20ac80548186"
# Attribution, can be None if not applicable
ATTRIBUTION = "The Danish Agency for Agriculture"

# License of the data, either
# 1. a SPDX license identifier (including "dl-de/by-2-0" / "dl-de/zero-2-0"), or
LICENSE = "CC0-1.0"
# 2. a STAC Link Object with relation type "license"
# LICENSE = {"title": "CC-BY-4.0", "href": "https://creativecommons.org/licenses/by/4.0/", "type": "text/html", "rel": "license"}

# Map original column names to fiboa property names
# You also need to list any column that you may have added in the MIGRATION function (see below).
COLUMNS = {    
    'MARKBLOKNR' : 'id', # fiboa core field , TODO MARKBLOKNR-id conversion is needed.     
    'GEOMETRISK' : 'area',# fiboa core field i.e total area = eligible area + ineligible area
    'TARAAREAL': 'ineligible_area', #fiboa custom field
    'STOETPROC' : 'support_proc',  # fiboa custom field - translated. Supported Scheme. Currently all values are NaN
    'GB_FRADRAG' : 'deduction', # fiboa custom field - translated 
    'MB_TYPE' : 'block_type', #fiboa custom field
    'GB_AREAL': 'eligible_area', # fiboa custom field i.e. eligible area
    'geometry':'geometry'# fiboa core field
}

# Add columns with constant values.
# The key is the column name, the value is a constant value that's used for all rows.
ADD_COLUMNS = {
    "determination_datetime": "2021-01-01T00:00:00Z"
}

# A list of implemented extension identifiers
EXTENSIONS = []

# Functions to migrate data in columns to match the fiboa specification.
# Example: You have a column area_m in square meters and want to convert
# to hectares as required for the area field in fiboa.
# Function signature:
#   func(column: pd.Series) -> pd.Series
COLUMN_MIGRATIONS = {
    'MB_TYPE': lambda column: column.map({'OMD' : 'Rotational crops', 'PGR' : 'Permanent grass', 'ING' : 'None', 'PAF' : 'Permanent crops', 'MIX' : 'Mixed permanent grass and arable land', 'VKS' : 'Plants under greenhouse/ nurseries /potted plants', 'LDP' : 'Afforestation'}),
}

# Filter columns to only include the ones that are relevant for the collection,
# e.g. only rows that contain the word "agriculture" but not "forest" in the column "land_cover_type".
# Lamda function accepts a Pandas Series and returns a Series or a Tuple with a Series and True to inverse the mask.
COLUMN_FILTERS = {
    'MB_TYPE': lambda col: (col.isin(["Rotational crops", "Permanent crops", "Plants under greenhouse/ nurseries /potted plants"]), True)
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
        'eligible_area': {
            'type': 'float',
            'exclusiveMinimum': 0
        },
        'ineligible_area': {
            'type': 'float',
            'exclusiveMinimum': 0
        },
        'deduction': {
            'type': 'float',
            'exclusiveMinimum': 0
        },
        'support_proc': {
            'type': 'float',
            'exclusiveMinimum': 0
        },
        'block_type': {
            'type': 'string',
            'enum': [ 'Rotational crops',  'Permanent grass', 'None', 'Permanent crops', 'Mixed permanent grass and arable land', 'Plants under greenhouse/ nurseries /potted plants',  'Afforestation']
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
