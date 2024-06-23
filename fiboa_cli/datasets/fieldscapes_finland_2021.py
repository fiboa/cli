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

# original data : https://www.ruokavirasto.fi/en/about-us/open-information/spatial-data-sets/
SOURCES = "/mnt/c/Snehal/Kerner Lab/tge-fiboa/finland/all_parcels.gpkg" # data subset for FieldScapes

# Unique identifier for the collection
ID = "fieldscapes_finland_2021"
# Title of the collection
TITLE = "Field boundaries for Finland (FieldScapes)"

# Description of the collection. Can be multiline and include CommonMark.
# Adapted from : https://www.paikkatietohakemisto.fi/geonetwork/srv/eng/catalog.search#/metadata/d85fbeba-fe58-4244-83d4-6f6dd8e4208d
DESCRIPTION = """The Finnish Food Authority has published spatial data sets under the INSPIRE Directive since 2020. Since 2023, the published data has contained high-value data sets.

Arable land is land cultivated for plant production or fallow land available for cultivation Fallen land is arable agricultural land that is not used for agricultural production. Fallow land can be either field or permanent grass. Fallow land must be kept open so that it is suitable for grazing or cultivation without having to prepare it with anything other than conventional agricultural methods and machinery. Take care to keep the area open if necessary, e.g. by mowing or grazing.

Permanent turf is a block that is used to grow hay and grass plants that have been in the same place for more than 5 years, either by self-renewal or by sowing. The land use type of permanent grass can be a field or natural pasture and meadow. A maximum of 50 trees per hectare are allowed to grow scattered on permanent lawns. Tree-like plants over two meters tall, with one trunk or several trunks joined together at the base, are considered trees. Trees are also plants with woody stems that are 0.5–2 meters tall and are not suitable for feeding farm animals. Leafy shrubs and saplings of deciduous trees suitable for feeding farm animals may grow in the area if they are less than 50 percent of the area of ​​the eligible growth block. The share of hay and grass fodder plants must be more than 50 percent of the eligible area of ​​the growth block, even in those blocks of permanent grass that have either trees or leafy bushes or both.

Natural pastures are areas of permanent grass, the land use type of which is natural pasture and meadow.

A permanent plant means a block of land use type, which has plants that are not part of the crop rotation, which are grown for at least 5 years and from which a repeated harvest is obtained. These plants include, for example, fruit trees, berry bushes and ornamental plants.q
"""

# Provider name, can be None if not applicable, must be provided if PROVIDER_URL is provided
PROVIDER_NAME = "National Land Survey of Finland"
# URL to the homepage of the data or the provider, can be None if not applicable
PROVIDER_URL = "https://www.paikkatietohakemisto.fi/geonetwork/srv/eng/catalog.search#/metadata/d85fbeba-fe58-4244-83d4-6f6dd8e4208d"
# Attribution, can be None if not applicable
ATTRIBUTION = " The Finnish Food Authority"

# License of the data, either
# 1. a SPDX license identifier (including "dl-de/by-2-0" / "dl-de/zero-2-0"), or
LICENSE = "CC-BY-4.0"
# 2. a STAC Link Object with relation type "license"
# LICENSE = {"title": "CC-BY-4.0", "href": "https://creativecommons.org/licenses/by/4.0/", "type": "text/html", "rel": "license"}

# Map original column names to fiboa property names
# You also need to list any column that you may have added in the MIGRATION function (see below).
COLUMNS = {
    'id' : 'id', # fiboa core field , TODO MARKBLOKNR-id conversion is needed.   
    'area' : 'area',  # fiboa core field
    'MAANKAYTTOLAJI' : 'land_use',#fiboa custom field 
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
    'MAANKAYTTOLAJI': lambda column: column.map({'AL' : 'Arable Land', 'PC' : 'Permanent Grass', 'PG': 'Permanent Plant'})
}

# Filter columns to only include the ones that are relevant for the collection,
# e.g. only rows that contain the word "agriculture" but not "forest" in the column "land_cover_type".
# Lamda function accepts a Pandas Series and returns a Series or a Tuple with a Series and True to inverse the mask.
COLUMN_FILTERS = {
    "MAANKAYTTOLAJI": lambda col: (col.isin(["Arable Land"]), True)
}

# Custom function to migrate the GeoDataFrame if the other options are not sufficient
# This should be the last resort!
# Function signature:
#   func(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame
def migrate(gdf):
    gdf = gdf.to_crs(epsg=3067)  # Convert to a projected CRS (e.g., EPSG:3067 for Finland)
    gdf['area'] = gdf['geometry'].area * 0.0001
    gdf['id'] = range(1, len(gdf) + 1) # auto incremented id
    gdf = gdf.to_crs(epsg=4326)
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
        "land_use": {
            "type": "string",
            "enum" : [ 'Arable Land',  'Permanent Grass', 'Permanent Plant']
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
