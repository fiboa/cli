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

# original dataset : https://www.geodata.se/geodataportalen/srv/swe/catalog.search;jsessionid=6C2D281619D69AC2356E1BD4C1923A3A#/search?resultType=swe-details&_schema=iso19139*&type=dataset%20or%20series&from=1&to=20&fast=index&_content_type=json&sortBy=relevance&or=jordbruksblock
SOURCES = "/mnt/c/Snehal/Kerner Lab/tge-fiboa/sweden/all_parcels.gpkg"  # data subset for FieldScapes

# Unique identifier for the collection
ID = "fieldscapes_sweden_2021"
# Title of the collection
TITLE = "Field boundaries for Sweden (FieldScapes)"
# Description of the collection. Can be multiline and include CommonMark.

# Adapted from https://collections.eurodatacube.com/sweden-lpis/
DESCRIPTION = """Sweden's Land Parcel Identification System (LPIS) data collection (also agricultural blocks/ 'jordbruksblock') is managed by the Swedish Board of Agriculture, and also made available on the INSPIRE Geoportal. The Swedish agricultural blocks are vector data containing information on maximum eligible agricultural land according to EU definitions. The agricultural blocks are used by the Swedish Board of Agriculture to administer support to farmers, therefore the collection does not include all agricultural land in Sweden, but only the parts that a farmer has sought support for at some time.

A block is a polygon/surface that delimits an area of ​​agricultural land. A block is delimited by fixed boundaries. Examples of fixed boundaries are roads, stone walls, forests and buildings.

The dataset Agricultural blocks contains approximately 1,143,000 blocks. Of these, approximately 891,000 are arable land blocks and approximately 252,000 pasture land blocks. The total area is 3.2 million hectares, of which 2.7 million hectares are arable land and 510,000 hectares are pasture land. The average area for the arable land blocks is 3.03 ha and for the pasture blocks the corresponding figure is 2.03 ha.
"""

# Bounding box of the data in WGS84 coordinates
BBOX = [7.8685145620,53.3590675115,11.3132037822,55.0573747014]

# Provider name, can be None if not applicable, must be provided if PROVIDER_URL is provided
PROVIDER_NAME = "The Swedish Agency for Agriculture"
# URL to the homepage of the data or the provider, can be None if not applicable
PROVIDER_URL = "https://www.geodata.se/geodataportalen/srv/swe/catalog.search;jsessionid=6C2D281619D69AC2356E1BD4C1923A3A#/metadata/df439ba5-014e-44ec-86cb-ddb9e5ba306c"
# Attribution, can be None if not applicable
ATTRIBUTION = "The Swedish Agency for Agriculture"

# License of the data, either
# 1. a SPDX license identifier (including "dl-de/by-2-0" / "dl-de/zero-2-0"), or

# Invalid License Identifier as of now. Link : https://www.geodata.se/geodataportalen/srv/swe/catalog.search;jsessionid=6C2D281619D69AC2356E1BD4C1923A3A#/metadata/df439ba5-014e-44ec-86cb-ddb9e5ba306c
LICENSE = "No restrictions on public access" # TODO : how to add such identifiers?
 
# 2. a STAC Link Object with relation type "license"
# LICENSE = {"title": "CC-BY-4.0", "href": "https://creativecommons.org/licenses/by/4.0/", "type": "text/html", "rel": "license"}

# Map original column names to fiboa property names
# You also need to list any column that you may have added in the MIGRATION function (see below).
COLUMNS = {
    'AREAL': 'area',# fiboa core field
    'BLOCKID':'id',# fiboa core field
    'REGION':'region', #fiboa custom field 
    'KATEGORI': 'land_cover_category',  #fiboa custom field 
    'AGOSLAG':'land_cover_class', #fiboa custom field 
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
    'AGOSLAG': lambda column: column.map({'AKER' : 'Farmland', 'AKER_PERMGRAS' : 'Cropland – long-lying grassland', 'BETE' : 'Pastures', 'AKER_PERMGROD' : 'Cropland – permanent crops', 'ÖVRM' : 'Other land', 'OKÄNT' : 'Unknown','VÅTMARK': 'Wetland'})
}

# Filter columns to only include the ones that are relevant for the collection,
# e.g. only rows that contain the word "agriculture" but not "forest" in the column "land_cover_type".
# Lamda function accepts a Pandas Series and returns a Series or a Tuple with a Series and True to inverse the mask.
COLUMN_FILTERS = {
    'AGOSLAG': lambda col: (col.isin(["Farmland", "Cropland – permanent crops"]), True)
}

# Custom function to migrate the GeoDataFrame if the other options are not sufficient
# This should be the last resort!
# Function signature:
#   func(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame
MIGRATION = None

# Schemas for the fields that are not defined in fiboa
# Keys must be the values from the COLUMNS dict, not the keys
MISSING_SCHEMAS = {
    "properties": {
        'land_cover_category': {
            'type': 'string'
        },
        'land_cover_class': {
            'type': 'string'
        },
        'region': {
            'type': 'string'
        }
    }
}


# Conversion function, usually no changes required
def convert(output_file, input_files = None, cache = None, source_coop_url = None, collection = False, compression = None):
    convert_(
        output_file,
        cache,
        SOURCES,
        COLUMNS,
        ID,
        TITLE,
        DESCRIPTION,
        input_files=input_files,
        provider_name=PROVIDER_NAME,
        provider_url=PROVIDER_URL,
        source_coop_url=source_coop_url,
        extensions=EXTENSIONS,
        missing_schemas=MISSING_SCHEMAS,
        column_migrations=COLUMN_MIGRATIONS,
        column_filters=COLUMN_FILTERS,
        migration=MIGRATION,
        attribution=ATTRIBUTION,
        store_collection=collection,
        license=LICENSE,
        compression=compression,
    )