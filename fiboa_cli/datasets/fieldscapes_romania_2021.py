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
SOURCES = "/mnt/c/Snehal/Kerner Lab/tge-fiboa/romania/t_all_parcels.gpkg"

# Unique identifier for the collection
ID = "fieldscapes_romania_2021"
# Title of the collection
TITLE = "Field boundaries for Romania (FieldScapes)"
# Description of the collection. Can be multiline and include CommonMark.
# Adapted from : https://data.europa.eu/data/datasets/092425a1-90c6-4461-b1a6-6f5b0f72748f?locale=ro
DESCRIPTION = """The data set includes the land cover layer from the Romanian side of the Romania-Bulgaria cross-border area (Mehedinți, Dolj, Olt, Teleorman, Giurgiu, Călărași, Constanța counties), elaborated within the project "Common strategy for territorial development of the cross-border Romania-Bulgaria area", code MIS-ETC 171, financed from the Romania-Bulgaria Cross-Border Cooperation Program 2007-2013.

The data set is published in the WGS 84 / UTM zone 35N coordinate system (to be compatible with the similar data set on the Bulgarian side).

The dataset conforms to the conceptual framework described in the Land Cover Data Specifications for the Implementation of the INSPIRE Directive (version 3.0). The information layer was elaborated on the basis of a methodology carried out within the project, which proceeded as follows: - analysis and harmonization of the land cover classification system; - obtaining and processing reference data, listed below; - checking and validating the quality of spatial data produced.
The data set regarding the land cover layer constitutes one of the common resources necessary for the elaboration of the common territorial development strategy and for monitoring the impact for the Romania-Bulgaria cross-border area.
"""

# Provider name, can be None if not applicable, must be provided if PROVIDER_URL is provided
# https://github.com/maja601/EuroCrops/wiki/Romania
PROVIDER_NAME = "Eurocrop"
# URL to the homepage of the data or the provider, can be None if not applicable
# Originally from : https://data.europa.eu/data/datasets/092425a1-90c6-4461-b1a6-6f5b0f72748f?locale=ro
PROVIDER_URL = "https://zenodo.org/records/8229128/files/RO_ny.zip?download=1"
# Attribution, can be None if not applicable
ATTRIBUTION = "Ministry of Regional Development and Public Administration"

# License of the data, either
# 1. a SPDX license identifier (including "dl-de/by-2-0" / "dl-de/zero-2-0"), or
LICENSE = "CC-BY-4.0"
# 2. a STAC Link Object with relation type "license"
# LICENSE = {"title": "CC-BY-4.0", "href": "https://creativecommons.org/licenses/by/4.0/", "type": "text/html", "rel": "license"}

# Map original column names to fiboa property names
# You also need to list any column that you may have added in the MIGRATION function (see below).
COLUMNS = {
    'id':'id', # fiboa core field
    'COUNTRYCOD' : 'country',
    'LC_MAPCODE' : 'land_surface_code',
    'LC_CLASS_E' : 'land_surface',
    'NOTE_' : 'note', 
    'SOURCE' : 'source', # data source 
    'AREA_HA' : 'area', # fiboa core field , in sq. m 
    'EC_hcat_n' : 'HCAT_crop_name', # added in eurocrops 
    'EC_trans_n' : 'crop_name_translated',# added in eurocrops 
    'geometry' :'geometry'# fiboa core field
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
    "AREA_HA": lambda column: column * 0.0001,
    "EC_hcat_n": lambda column: column.str.strip().str.lower(),
    'NOTE_': lambda column: column.map({ 'ZONA FORESTIERA': 'FOREST AREA',
        'HR ZONA FORESTIERA': 'HR FOREST AREA',
        'TA ARABIL': 'TA ARABIL',
        'HN Vegetatie mlastinoasa': 'HN Marsh Vegetation',
        'PN NEPRODUCTIV': 'NON-PRODUCT PN',
        'PA ZONA FORESTIERA': 'PA FOREST AREA',
        'TA ZONA FORESTIERA': 'TA FOREST AREA',
        'ARABIL': 'ARABIL',
        'HR LUCIU APA': 'HR LUCIU APA',
        'PP ARABIL': 'PP ARABIL',
        'DR NEPRODUCTIV': 'DR NON-PRODUCTIVE',
        'LUCIU APA': 'LUCIU APA',
        'URBAN': 'URBAN',
        'PP PAJISTI': 'PP PAJISTI',
        'CP LIVADA': 'CP LIVADA',
        'VI ARABIL': 'VI ARABIL',
        'HB Vegetatie mlastinoasa': 'HB Marsh Vegetation',
        'Vegetatie mlastinoasa': 'Marsh Vegetation',
        'DR ZONA FORESTIERA': 'DR FOREST AREA',
        'TA URBAN': 'TA URBAN',
        'PA ARABIL': 'PA ARABIL',
        'NEPRODUCTIV': 'NON-PRODUCTIVE',
        'PAJISTI': 'PAJISTI',
        'HR ARABIL': 'HR ARABIL',
        'HN ZONA FORESTIERA': 'HN FOREST AREA',
        'CC URBAN': 'CC URBAN',
        'MX ZONA FORESTIERA': 'MX FOREST AREA',
        'PP URBAN': 'PP URBAN',
        'PA URBAN': 'PA URBAN',
        'VI URBAN': 'VI URBAN',
        'HB LUCIU APA': 'HB LUCIU APA',
        'HN URBAN': 'HN URBAN',
        'CC NEPRODUCTIV': 'CC NON-PRODUCTIVE',
        'MX ARABIL': 'MX ARABIL',
        'PN ZONA FORESTIERA': 'PN FOREST AREA',
        'LIVADA': 'LIVADA',
        'DR URBAN': 'DR URBAN',
        'HR Vegetatie mlastinoasa': 'HR Marsh Vegetation',
        'MX URBAN': 'MX URBAN',
        'HR URBAN': 'HR URBAN',
        'XX ZONA FORESTIERA': 'XX FOREST AREA',
        'HR PAJISTI': 'HR PAJISTI',
        'TA PAJISTI': 'TA PAJISTI',
        'HN NEPRODUCTIV': 'NON-PRODUCT HN'
        }),

}

# Filter columns to only include the ones that are relevant for the collection,
# e.g. only rows that contain the word "agriculture" but not "forest" in the column "land_cover_type".
# Lamda function accepts a Pandas Series and returns a Series or a Tuple with a Series and True to inverse the mask.
COLUMN_FILTERS = {
    'EC_hcat_n': lambda col: (col.isin(['arable_crops' 'rice']), True) # something is wrong here
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
        "country": {
            "type": "string"
        },
        "land_surface_code": {
            "type": "string"
        },
        "land_surface": {
            "type": "string"
        },
        "note": {
            "type": "string"
        },
        "source": {
            "type": "string"
        },
        "HCAT_crop_name": {
            "type": "string"
        },
        "crop_name_translated": {
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
