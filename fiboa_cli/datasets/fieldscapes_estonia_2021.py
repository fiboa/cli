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
SOURCES = "/mnt/c/Snehal/Kerner Lab/tge-fiboa/estonia/all_parcels.gpkg" # data subset for FieldScapes

# Unique identifier for the collection
ID = "fieldscapes_estonia_2021"
# Title of the collection
TITLE = "Field boundaries for Estonia (FieldScapes)"
# Description of the collection. Can be multiline and include CommonMark.


# https://metadata.geoportaal.ee/geonetwork/srv/est/catalog.search#/metadata/pria:pollud
# https://metadata.geoportaal.ee/geonetwork/srv/est/catalog.search#/metadata/2fa494d3-3f1d-4f76-9866-bedd005cada6
DESCRIPTION = """Geospatial Aid Application Estonia Agricultural parcels."""
# Bounding box of the data in WGS84 coordinates
BBOX = [24.7007465000000010,27.3816513899999983, 57.6345101000000000 , 58.9531708800000018]


# Provider name, can be None if not applicable, must be provided if PROVIDER_URL is provided
PROVIDER_NAME = "EuroCrop" # INSPIRE Theme originally
# URL to the homepage of the data or the provider, can be None if not applicable
PROVIDER_URL = "https://zenodo.org/records/8229128/files/EE_2021.zip?download=1"
# Attribution, can be None if not applicable
ATTRIBUTION = "Agricultural Registers and Information Agency"

# License of the data, either
# 1. a SPDX license identifier (including "dl-de/by-2-0" / "dl-de/zero-2-0"), or
LICENSE = "CC-3.0"
# 2. a STAC Link Object with relation type "license"
# LICENSE = {"title": "CC-BY-4.0", "href": "https://creativecommons.org/licenses/by/4.0/", "type": "text/html", "rel": "license"}

# Map original column names to fiboa property names
# You also need to list any column that you may have added in the MIGRATION function (see below).
COLUMNS = {
    'pollu_id' : 'id',  # fiboa core field
    'pindala_ha' : 'area', # fiboa core field
    'taotletud_' : 'requested_culture',
    'taotletu_1' : 'requested_land_use',
    'niitmise_t' : 'mowing_detection_status',
    'niitmise_1' : 'mowing_detection_period',
    'taotletu_2' : 'requested_support',
    'EC_trans_n' : 'EC_trans_n',
    'EC_hcat_n' : 'EC_hcat_n',
    
    'viimase_mu' : 'determination_datetime',
    'geometry':'geometry'  # fiboa core field
}


# Add columns with constant values.
# The key is the column name, the value is a constant value that's used for all rows.
ADD_COLUMNS = {
    # "determination_datetime": "2021-12-31T00:00:00Z"
}

# A list of implemented extension identifiers
EXTENSIONS = []

# Functions to migrate data in columns to match the fiboa specification.
# Example: You have a column area_m in square meters and want to convert
# to hectares as required for the area field in fiboa.
# Function signature:
#   func(column: pd.Series) -> pd.Series
COLUMN_MIGRATIONS = {
    'viimase_mu': lambda column: pd.to_datetime(column, format='%Y/%m/%d %H:%M:%S.%f').dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
    'taotletu_1': lambda column: column.map({'Karjatamine väljaspool põllumaj. maad': 'Grazing outside the farmhouse. land', 'Püsirohumaa': 'Permanent grass land', 'Põllukultuurid': 'Arable crops','Tagasirajatud rohumaa': 'Reestablished grassland', 'Püsikultuurid': 'Permanent crops','Mustkesa': 'Mustkesa','Keskkonnatundlik püsirohumaa': 'Environmentally sensitive permanent grassland'}),
    'niitmise_t': lambda column: column.map({'Niidetud': 'Mowed', 'Ei kuulu jälgimisele': 'Not Monitored','Hilinenud niidetud': 'Late Mowed', 'Tulemus vajab täpsustamist': 'Result needs clarification', 'Niitmata': 'Uncut', 'Andmed puuduvad': 'No data','Madal biomass': 'Low Biomass'})
}


# Filter columns to only include the ones that are relevant for the collection,
# e.g. only rows that contain the word "agriculture" but not "forest" in the column "land_cover_type".
# Lamda function accepts a Pandas Series and returns a Series or a Tuple with a Series and True to inverse the mask.
COLUMN_FILTERS = {
    "taotletu_1": lambda col: (col.isin(['Arable crops', 'Permanent crops']), True)
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
        "requested_culture": {
            "type": "string"
        },

        "requested_land_use": {
            "type": "string",
            "enum" :['Grazing outside the farmhouse. land', 'Permanent grass land',  'Arable crops','Reestablished grassland', 'Permanent crops', 'Mustkesa', 'Environmentally sensitive permanent grassland']
        },

        "mowing_detection_status": {
            "type": "string"
        },

        "mowing_detection_period": {
            "type": "string"
        },

        "last_edit": {
            "type": "date-time"
        },

        "requested_support": {
            "type": "string"
        },
        "EC_trans_n": {
            "type": "string"
        },
        "EC_hcat_n": {
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
