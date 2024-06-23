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

# original data : https://service.pdok.nl/rvo/brpgewaspercelen/atom/v1_0/basisregistratie_gewaspercelen_brp.xml
SOURCES = "/mnt/c/Snehal/Kerner Lab/tge-fiboa/netherlands/all_parcels.gpkg" # data subset for FieldScapes

# Unique identifier for the collection
ID = "fieldscapes_netherlands_2022"
# Title of the collection
TITLE = "Field boundaries for Netherlands (FieldScapes)"
# Description of the collection. Can be multiline and include CommonMark.

# original dataset : https://service.pdok.nl/rvo/brpgewaspercelen/atom/v1_0/basisregistratie_gewaspercelen_brp.xml
DESCRIPTION = """BRP - Crop plots consists of the location of agricultural plots linked to the crop grown. The file is a selection of information from the Basic Register of Plots (BRP) of the Netherlands Enterprise Agency. The boundaries of the agricultural plots are based on the Agricultural Area of ​​the Netherlands (AAN).

The user of the plot must annually register his crop plots and indicate which crop is grown on the plot in question. A dataset is generated for each year with reference date May 15."""

# Provider name, can be None if not applicable, must be provided if PROVIDER_URL is provided
PROVIDER_NAME = "PDOK Control"
# URL to the homepage of the data or the provider, can be None if not applicable
PROVIDER_URL = "https://service.pdok.nl/rvo/brpgewaspercelen/atom/v1_0/basisregistratie_gewaspercelen_brp.xml"
# Attribution, can be None if not applicable
ATTRIBUTION = "The Netherlands Enterprise Agency"

# License of the data, either
# 1. a SPDX license identifier (including "dl-de/by-2-0" / "dl-de/zero-2-0"), or
LICENSE = "CC0-1.0"
# 2. a STAC Link Object with relation type "license"
# LICENSE = {"title": "CC-BY-4.0", "href": "https://creativecommons.org/licenses/by/4.0/", "type": "text/html", "rel": "license"}

# Map original column names to fiboa property names
# You also need to list any column that you may have added in the MIGRATION function (see below).
COLUMNS = {
    'id' : 'id', # fiboa core field 
    'area' : 'area', # fiboa core field 
    'category':'crop_category',
    'gewas':'crop_type',
    'status':'status',    
    'geometry':'geometry',    # fiboa core field 
}


# Add columns with constant values.
# The key is the column name, the value is a constant value that's used for all rows.
ADD_COLUMNS = {
    "determination_datetime": "2022-01-01T00:00:00Z" # fiboa core field 
}

# A list of implemented extension identifiers
EXTENSIONS = []

# Functions to migrate data in columns to match the fiboa specification.
# Example: You have a column area_m in square meters and want to convert
# to hectares as required for the area field in fiboa.
# Function signature:
#   func(column: pd.Series) -> pd.Series
COLUMN_MIGRATIONS = {
    'category': lambda column: column.map({'Grasland':'Grassland', 'Bouwland':'Arable land', 'Overige':'Other', 'Braakland':'Fallow land', 'Natuurterrein':'Natural area'}),
    'status': lambda column: column.map({'Actueel' : 'Current'}) 
}

# Filter columns to only include the ones that are relevant for the collection,
# e.g. only rows that contain the word "agriculture" but not "forest" in the column "land_cover_type".
# Lamda function accepts a Pandas Series and returns a Series or a Tuple with a Series and True to inverse the mask.
COLUMN_FILTERS = {
    "category": lambda col: (col.isin(["Arable land"]), True)
}

# Custom function to migrate the GeoDataFrame if the other options are not sufficient
# This should be the last resort!
# Function signature:
#   func(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame

def migrate(gdf):
    gdf = gdf.to_crs(epsg=28992)  # Convert to a projected CRS
    gdf['area'] = gdf['geometry'].area * 0.0001
    gdf['id'] = range(1, len(gdf) + 1)
    gdf = gdf.to_crs(epsg=4326) 
    return gdf

MIGRATION = migrate

# Schemas for the fields that are not defined in fiboa
# Keys must be the values from the COLUMNS dict, not the keys
MISSING_SCHEMAS = {
    "properties": {
        "crop_type": {
            "type": "string"
        },
        "crop_category": {
            "type": "string",
            "enum" : ['Grassland', 'Arable land', 'Other','Fallow land', 'Natural area']
        },
        "status": {
            "type": "string"
        }
        
    }
}


# Conversion function, usually no changes required
def convert(output_file,  input_files = None, cache = None, source_coop_url = None, collection = False, compression = None):
    """
    Converts the field boundary datasets to fiboa.

    For reference, this is the order in which the conversion steps are applied:
    0. Read GeoDataFrame from file
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
    cache): Path to a cached file of the data. Default: None.
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
        provider_name=PROVIDER_NAME,
        provider_url=PROVIDER_URL,
        source_coop_url=source_coop_url,
        extensions=EXTENSIONS,
        missing_schemas=MISSING_SCHEMAS,
        column_additions=ADD_COLUMNS,
        column_migrations=COLUMN_MIGRATIONS,
        column_filters=COLUMN_FILTERS,
        migration=MIGRATION,
        attribution=ATTRIBUTION,
        store_collection=collection,
        license=LICENSE,
        compression=compression,
    )
