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
SOURCES = "/mnt/c/Snehal/Kerner Lab/tge-fiboa/belgium/all_parcels.gpkg"

# Unique identifier for the collection
ID = "fieldscapes_belgium_2021"
# Title of the collection
TITLE = "Field boundaries for Belgium (FieldScapes)"
# Description of the collection. Can be multiline and include CommonMark.
DESCRIPTION = """The inventory of these plots is done annually in the context of the payment of the (co-financed) European agricultural subsidies and the Flemish manure legislation. The dataset has an informative value for a generalized use and is in no way intended for control purposes or individualized use.

"""

# Provider name, can be None if not applicable, must be provided if PROVIDER_URL is provided
PROVIDER_NAME = "The Agriculture and Sea Fisheries Agency"
# URL to the homepage of the data or the provider, can be None if not applicable

# Original Source : https://landbouwcijfers.vlaanderen.be/open-geodata-landbouwgebruikspercelen
PROVIDER_URL = "https://github.com/maja601/EuroCrops/wiki/Belgium"
# Attribution, can be None if not applicable
ATTRIBUTION = "The Agriculture and Sea Fisheries Agency"

# License of the data, either
# 1. a SPDX license identifier (including "dl-de/by-2-0" / "dl-de/zero-2-0"), or
# LICENSE = "No restrictions on public access"
# 2. a STAC Link Object with relation type "license"
LICENSE = {"title": "No restrictions on public access", "href": "https://metadata.vlaanderen.be/srv/dut/catalog.search#/metadata/d869db4a-73f4-470e-b5ca-a0f7cd3ab585", "type": "text/html", "rel": "license"}

# Map original column names to fiboa property names
# You also need to list any column that you may have added in the MIGRATION function (see below).
COLUMNS = {
'id' : 'id', # fiboa core field
'GRAF_OPP' : 'area', # fiboa core field
'GWSCOD_V' : 'pre_crop_code',
'GWSNAM_V' : 'pre_crop_name',
'GWSCOD_H' : 'crop_code',
'GWSNAM_H' : 'crop_name',
'GWSNAM_N2' : 'second_post_crop_name',
'EC_trans_n' : 'EC_trans_n',
'EC_hcat_n' : 'EC_hcat_n',
'geometry'  : 'geometry' # fiboa core field
}

# Add columns with constant values.
# The key is the column name, the value is a constant value that's used for all rows.
ADD_COLUMNS = {
    "determination_datetime": "2022-03-15T00:00:00Z" # Initial submission : April 30, 2021, final submission : March 15, 2022
}

# A list of implemented extension identifiers
EXTENSIONS = []

# Functions to migrate data in columns to match the fiboa specification.
# Example: You have a column area_m in square meters and want to convert
# to hectares as required for the area field in fiboa.
# Function signature:
#   func(column: pd.Series) -> pd.Series
COLUMN_MIGRATIONS = {
     "EC_hcat_n": lambda column: column.str.strip().str.lower()
}


# Filter columns to only include the ones that are relevant for the collection,
# e.g. only rows that contain the word "agriculture" but not "forest" in the column "land_cover_type".
# Lamda function accepts a Pandas Series and returns a Series or a Tuple with a Series and True to inverse the mask.
COLUMN_FILTERS = {
    "EC_hcat_n": lambda col: (col.isin([ 'permanent_crops_perennial', 'beans', 'parsnips', 'asparagus', 'brussels_sprouts',
        'onions', 'rhubarb', 'spinach', 'cauliflower', 'kale', 'red_cabbage', 'carrots_daucus',
        'leek', 'celeriac', 'savoy_cabbage', 'celery', 'fresh_vegetables', 'miscanthus_silvergrass',
        'potatoes', 'sweet_potatoes', 'sugar_beet', 'peas', 'pumpkin_squash_gourd', 'strawberries',
        'broccoli', 'endive', 'white_cabbage', 'zucchini_courgette', 'lambs_lettuce_rapunzel',
        'iceberg', 'chrysanthemum', 'sod_turf', 'tomato', 'aubergine_eggplant', 'artichoke',
        'parsly', 'chervil', 'brassica_oleracea_cabbage', 'apples', 'fibre_crops', 'radish',
        'winter_common_soft_wheat', 'green_silo_maize', 'grain_maize_corn_popcorn',
        'spring_common_soft_wheat', 'winter_barley', 'spring_barley', 'winter_rye', 'triticale',
        'spelt', 'winter_rapeseed_rape', 'sunflower', 'rye', 'winter_oats', 'millet_sorghum',
        'hazelnuts_hazel', 'walnuts', 'chinese_cabbage', 'beetroot_beets', 'bell_pepper_paprika',
        'industrial_nonfood_crops', 'quinoa', 'summer_rapeseed_rape', 'turnips', 'soy_soybeans',
        'kohlrabi', 'blackcurrant_cassis', 'fodder_roots', 'barley', 'hemp_cannabis', 'leaf_celery',
        'cucumber_pickle', 'hops', 'tagetes', 'shallot', 'rocket_arugula', 'blackberry', 'mustard',
        'buckwheat', 'oilseed_crops', 'spring_rye']))
}

# Custom function to migrate the GeoDataFrame if the other options are not sufficient
# This should be the last resort!
# Function signature:
#   func(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame

def migrate(gdf):
    gdf['id'] = range(1, len(gdf) + 1) # auto incremented id
    return gdf

MIGRATION = migrate


# Custom function to execute actions on the the GeoDataFrame that are loaded from individual file.
# This is useful if the data is split into multiple files and columns should be added or changed
# on a per-file basis for example.
# The path contains the local path to the file that was read.
# The uri contains the URL that was read.
# Function signature:
#   func(gdf: gpd.GeoDataFrame, path: string, uri: string) -> gpd.GeoDataFrame
FILE_MIGRATION = None



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
        'pre_crop_code': {
            "type": "string"
        },
        'pre_crop_name': {
            "type": "string"
        },
        'crop_code': {
            "type": "string"
        },
        'crop_name': {
            "type": "string"
        },
        'second_post_crop_name': {
            "type": "string"
        },
        'EC_trans_n': {
            "type": "string"
        },
        'EC_hcat_n': {
            "type": "string"
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
