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

# original source : https://www.apprrr.hr/wp-content/uploads/nipp/land_parcels.gpkg
SOURCES = "/mnt/c/Snehal/Kerner Lab/tge-fiboa/croatia/all_parcels.gpkg" # data subset for FieldScapes

# Unique identifier for the collection
ID = "fieldscapes_croatia_2023"
# Title of the collection
TITLE = "Field boundaries for Croatia (FieldScapes)"
# Description of the collection. Can be multiline and include CommonMark.

# Adapted from : https://www.apprrr.hr/prostorni-podaci-servisi/
DESCRIPTION = """ARKOD is a record of the use of agricultural land in the territory of the Republic of Croatia, which is maintained in digital graphic form by the Agency for Payments.

ARKOD plots represent uninterrupted areas of agricultural land cultivated by one farmer, classified according to the type of use of agricultural land from Annex I of the Ordinance on records of use of agricultural land

Registration of agricultural land - vectorization of ARKOD polygons is carried out by the method of photointerpretation of agricultural land on DOF bases on a scale of 1:5000 in branches of the Agency for Payments, statements of farmers on the use of agricultural land with proof of ownership or possession. 
"""

# Bounding box of the data in WGS84 coordinates
BBOX = [16.5279565899699001,18.4786279156176008,45.1442638216278027, 46.1648742887660006]


# Provider name, can be None if not applicable, must be provided if PROVIDER_URL is provided
PROVIDER_NAME = "The Agency for Payments in Agriculture, Fisheries and Rural Development"
# URL to the homepage of the data or the provider, can be None if not applicable
PROVIDER_URL = "https://www.apprrr.hr/prostorni-podaci-servisi/"
# Attribution, can be None if not applicable
ATTRIBUTION = "The Agency for Payments in Agriculture, Fisheries and Rural Development"

# License of the data, either
# 1. a SPDX license identifier (including "dl-de/by-2-0" / "dl-de/zero-2-0"), or
LICENSE = "Open Data"
# 2. a STAC Link Object with relation type "license"
# LICENSE = {"title": "CC-BY-4.0", "href": "https://creativecommons.org/licenses/by/4.0/", "type": "text/html", "rel": "license"}

# Map original column names to fiboa property names
# You also need to list any column that you may have added in the MIGRATION function (see below).
COLUMNS = {
    'id': 'id', # fiboa core field
    'land_use_id' : 'land_use_id',
    'area' : 'area', # fiboa core field in sq. m
    'perim' : 'perimeter',
    'slope' : 'slope',
    'z_avg' : 'average_height',
    'eligibility_coef' : 'eligibility_coef',
    'mines_status' : 'mines_status',
    'water_protect_zone' : 'water_protect_zone',
    'anc' : 'restricted_surface',
    'anc_area' : 'restricted_surface_area',
    'rp' : 'vulnerable_areas',
    'tvpv' : 'high_degree_natural_value_meadow',
    'irrigation' : 'irrigation',
    'irrigation_source' : 'irrigation_source',
    'irrigation_type' : 'irrigation_type',
    'geometry' : 'geometry'  # fiboa core field
}

# Add columns with constant values.
# The key is the column name, the value is a constant value that's used for all rows.
ADD_COLUMNS = {
    "determination_datetime": "2023-01-01T00:00:00Z"
}

# A list of implemented extension identifiers
EXTENSIONS = []

# Functions to migrate data in columns to match the fiboa specification.
# Example: You have a column area_m in square meters and want to convert
# to hectares as required for the area field in fiboa.
# Function signature:
#   func(column: pd.Series) -> pd.Series

#  https://www.apprrr.hr/wp-content/uploads/NIPP/Interpretacija%20atributa.xlsx
COLUMN_MIGRATIONS = {
    'area': lambda column: column * 0.0001,
    'anc_area' :lambda column: column * 0.0001,
    'land_use_id': lambda column: column.map({200.0 : 'Arable land', 210.0 : 'Greenhouse', 310.0 : 'Meadow', 320.0 : 'Pasture', 321.0 : 'Karst pasture', 410.0 : 'Vineyard', 411.0 : 'Uprooted vineyard', 421.0 : 'Olive grove', 422.0 : 'Orchard', 430.0 : 'Cultures of short tours', 450.0 : 'Nursery', 490.0 : 'Mixed perennial plantations', 900.0 : 'Other', 910.0 : 'Temporarily unmaintained plot'}),
    'water_protect_zone': lambda column: column.map({'Vz0' : 'Width of the protective belt - 0 meters', 'Vz3': 'Width of the protective belt - 3 meters', 'Vz20': 'Width of the protective belt - 20 meters', 'Vz10': 'Width of the protective belt - 10 meters'}),
    'anc': lambda column: column.map({1.0 : 'Mountain mountain area', 2.0 : 'Area with special PPO restrictions', 3.0 : 'Area with significant natural restrictions ZPO'}),
    'tvpv': lambda column: column.map({1.0 : 'Continental lowland region', 2.0 : 'Mediterranean region', 3.0 :'Hilly mountain region'})
}

# Filter columns to only include the ones that are relevant for the collection,
# e.g. only rows that contain the word "agriculture" but not "forest" in the column "land_cover_type".
# Lamda function accepts a Pandas Series and returns a Series or a Tuple with a Series and True to inverse the mask.
COLUMN_FILTERS = {
    "land_use_id": lambda col: (col.isin(["Arable land"]), True)
}

# Custom function to migrate the GeoDataFrame if the other options are not sufficient
# This should be the last resort!
# Function signature:
#   func(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame
def migrate(gdf):
    gdf['id'] = range(1, len(gdf) + 1)
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


# Schemas for the fields that are not defined in fiboa
# Keys must be the values from the COLUMNS dict, not the keys
MISSING_SCHEMAS = {
    "properties": {
        "land_use_id": {
            "type": "string"
        }, 
         "slope": {
            "type": "float"
        }, 
         "average_height": {
            "type": "float"
        }, 
         "eligibility_coef": {
            "type": "float",
            'exclusiveMinimum': 0
        }, 

         "mines_status": {
            "type": "string"
        },  
         "land_use_id": {
            "type": "string"
        }, 
         "water_protect_zone": {
            "type": "string"
        }, 
        "restricted_surface": {
            "type": "string"
        }, 
        "restricted_surface_area": {
            "type": "float",
            'exclusiveMinimum': 0
        }, 
        "vulnerable_areas": {
            "type": "float",
            'exclusiveMinimum': 0
        }, 
         "high_degree_natural_value_meadow": {
            "type": "string"
        }, 
         "irrigation": {
            "type": "int32"
        }, 
         "irrigation_source": {
            "type": "float",
            'exclusiveMinimum': 0          
        }, 
         "irrigation_type": {
            "type": "float",
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
