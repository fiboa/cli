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
SOURCES = "/mnt/c/Snehal/Kerner Lab/tge-fiboa/france/all_parcels.gpkg"

# Unique identifier for the collection
ID = "fieldscapes_france_2020"
# Title of the collection
TITLE = "Field boundaries for France (FieldScapes)"
# Description of the collection. Can be multiline and include CommonMark.

# adapted from : https://geoservices.ign.fr/rpg#telechargementrpg2021
DESCRIPTION = """The graphic parcel register is a geographical database used as a reference for the processing of aid from the common agricultural policy (CAP).

The anonymized version distributed here as part of the public service for making reference data available contains graphic data for plots (basic land unit for farmers' declaration) with their main crop. This data has been produced by the Services and Payment Agency (ASP) since 2007.

In accordance with technical instruction DGPE/SDGP/2022-106 relating to the dissemination and use of data from the Graphical Parcel Register (RPG) of the Ministry of Agriculture and Food Sovereignty, agricultural plots instructed within the framework of the common agricultural policy are publicly disseminated.

The anonymous RPG data are vintage and contain plots corresponding to those declared for campaign N in their known situation and decided by the administration, generally on January 1 of year N+1. These data cover the entire French territory, including Mayotte and Saint-Martin, but excluding Saint-Barthélemy."""


# Provider name, can be None if not applicable, must be provided if PROVIDER_URL is provided
PROVIDER_NAME = "The Services and Payments Agency(ASP)"
# URL to the homepage of the data or the provider, can be None if not applicable
PROVIDER_URL = "https://geoservices.ign.fr/rpg#telechargementrpg2021"
# Attribution, can be None if not applicable

# https://geoservices.ign.fr/sites/default/files/2023-11/IGNF_RPG_2-1.html
ATTRIBUTION = "National Institute of Geographic and Forestry Information (IGN-F) "

# License of the data, either
# 1. a SPDX license identifier (including "dl-de/by-2-0" / "dl-de/zero-2-0"), or
# LICENSE = "Open Licence"
# 2. a STAC Link Object with relation type "license"
LICENSE = {"title": "Open Licence", "href": "https://geoservices.ign.fr/sites/default/files/2023-11/DC_DL_RPG_2-1_0.pdf", "type": "text/html", "rel": "license"}

# Map original column names to fiboa property names
# You also need to list any column that you may have added in the MIGRATION function (see below).
COLUMNS = {
'ID_PARCEL' : 'id',# fiboa core field
'SURF_PARC' : 'area',# fiboa core field
'CODE_CULTU' : 'crop_code',#fiboa custom field 
'CODE_GROUP' : 'crop_code_i',#fiboa custom field 
'geometry' : 'geometry'# fiboa core field
}

# Add columns with constant values.
# The key is the column name, the value is a constant value that's used for all rows.
ADD_COLUMNS = {
    "determination_datetime": "2020-12-31T00:00:00Z"
}

# A list of implemented extension identifiers
EXTENSIONS = []

# Functions to migrate data in columns to match the fiboa specification.
# Example: You have a column area_m in square meters and want to convert
# to hectares as required for the area field in fiboa.
# Function signature:
#   func(column: pd.Series) -> pd.Series
COLUMN_MIGRATIONS = {
     'CODE_CULTU': lambda column: column.str.strip().str.lower()
    #   'geometry': lambda column: column.apply(lambda geom: geom if geom.geom_type == 'Polygon' else geom.geoms[0] if geom.geom_type == 'MultiPolygon' else geom)
}

# Filter columns to only include the ones that are relevant for the collection,
# e.g. only rows that contain the word "agriculture" but not "forest" in the column "land_cover_type".
# Lamda function accepts a Pandas Series and returns a Series or a Tuple with a Series and True to inverse the mask.

#Features selected from : https://geoservices.ign.fr/sites/default/files/2023-02/REF_CULTURES_2021.csv
COLUMN_FILTERS = {
    'CODE_CULTU': lambda col: (col.isin(['ORH' 'BTH' 'PPR' 'CZH' 'TRN' 'BDH' 'LIP' 'TTH' 'ORP' 'CAG' 'EPE' 'SRS'
 'MCR' 'SOG' 'MPC' 'AVH' 'BTN' 'RDI' 'CEL' 'CHU' 'LDP' 'BTP' 'FLP' 'FVL'
 'LEC' 'MLT' 'FLA' 'AVP' 'SGH' 'CML' 'PHI' 'MPP' 'SOJ' 'MLS' 'CHT' 'PPO'
 'PCH' 'LIH' 'OAG' 'CRD' 'NOX' 'FNU' 'PTC' 'CPA' 'CHV' 'HBL' 'MLO' 'BDP'
 'PPA' 'OIG' 'CSE' 'LDH' 'PAN' 'PTF' 'HAR' 'PPP' 'CHA' 'TOM' 'PSL' 'POR'
 'CMB' 'CAR' 'ROQ' 'PAG' 'MOT' 'FNO' 'AIL' 'TAB' 'SGP' 'FRA' 'POT' 'CCT'
 'CMM' 'ANE' 'NVT' 'ART' 'CTG' 'CZP' 'BLT' 'NOS' 'PAS' 'LBF' 'LIF' 'MOL'
 'EPI' 'TTP' 'OEH' 'PVP' 'CES' 'FEV' 'TOP' 'MAC']), True)
}

# Custom function to migrate the GeoDataFrame if the other options are not sufficient
# This should be the last resort!
# Function signature:
#   func(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame
# def migration(gdf):
#         return gdf

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
        "crop_code": {
            "type": "string"
        },
        "crop_code_i": {
            "type": "uint8"
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
