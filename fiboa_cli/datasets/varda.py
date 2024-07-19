# Converter for Varda field boundary datasets to Fiboa.
# Aiming to have it work with both direct API access and with bulk download.

from ..convert_utils import convert as convert_

# File(s) to read the data from, usually publicly accessible URLs.
# Can read any (zipped) tabular data format that GeoPandas can read through read_file() or read_parquet().
# Supported protocols: HTTP(S), GCS, S3, or the local file system
#
# Multiple options are possible:
# 1. a single URL (filename must be in the URL). The file is read as is.
SOURCES = None

DATA_ACCESS = """
Data must be obtained from the Varda API, saved as .json files. Easiest way to try it out is 
to use the UI at https://fieldid.varda.ag/ and find some fields and click 'download .json' file, 
or else call the /boundaries endpoint - details at https://developer.varda.ag/fid.
"""

# A filter function for the layer in the file(s) to read.
# Set to None if the file contains only one layer or all layers should be read.
# Function signature:
#   func(layer: str, path: str) -> bool
LAYER_FILTER = None

# Unique identifier for the collection
ID = "varda"
# Geonames for the data (e.g. Country, Region, Source, Year)
SHORT_NAME = "Field Boundaries from Varda Global FieldID API" 
# Title of the collection
TITLE = "Field Boundaries from the Global FieldID system from Varda."
# Description of the collection. Can be multiline and include CommonMark.
DESCRIPTION = """TODO: Describe the dataset here."""

# A list of providers that contributed to the data.
# This should be an array of Provider Objects:
# https://github.com/radiantearth/stac-spec/blob/master/collection-spec/collection-spec.md#provider-object
PROVIDERS = [
    {
        "name": "Varda",
        "url": "https://www.varda.ag/",
        "roles": ["licensor"]
    }
]

# Attribution (e.g. copyright or citation statement as requested by provider).
# The attribution is usually shown on the map, in the lower right corner.
# Can be None if not applicable
ATTRIBUTION = "© 2024 Varda"

# License of the data, either
# 1. a SPDX license identifier (including "dl-de/by-2-0" / "dl-de/zero-2-0"), or
# LICENSE = "CC-BY-4.0"
# 2. a STAC Link Object with relation type "license"
LICENSE = {"title": "Proprietary", "href": "https://fieldid.varda.ag/help/terms-conditions", "type": "text/html", "rel": "license"}

# Map original column names to fiboa property names
# You also need to list any column that you may have added in the MIGRATION function (see below).
COLUMNS = {
    "geometry": "geometry",
    "id": "id"#,
    #"area": "area" Not working yet - it's a nested object and I don't know how to handle that.
}

# Add columns with constant values.
# The key is the column name, the value is a constant value that's used for all rows.
ADD_COLUMNS = {
}

# A list of implemented extension identifiers
EXTENSIONS = []

# Functions to migrate data in columns to match the fiboa specification.
# Example: You have a column area_m in square meters and want to convert
# to hectares as required for the area field in fiboa.
# Function signature:
#   func(column: pd.Series) -> pd.Series
COLUMN_MIGRATIONS = {
    # This isn't working - I don't know how to pull out the 'value' object from the JSON. 
    #lambda column: column.apply(lambda x: json.loads(x)["value"] * 0.0001)
}

# Filter columns to only include the ones that are relevant for the collection,
# e.g. only rows that contain the word "agriculture" but not "forest" in the column "land_cover_type".
# Lamda function accepts a Pandas Series and returns a Series or a Tuple with a Series and True to inverse the mask.
COLUMN_FILTERS = {
    #"land_cover_type": lambda col: (col.isin(["agrictulture"]), True)
}

# Custom function to migrate the full GeoDataFrame if the other options are not sufficient
# This should be the last resort!
# Function signature:
#   func(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame
MIGRATION = None

# Custom function to execute actions on the the GeoDataFrame that are loaded from individual file or layers.
# This is useful if the data is split into multiple files/layers and columns should be added or changed
# on a per-file/layer basis for example.
# The path contains the local path to the file that was read.
# The uri contains the URL that was read.
# The layer may contain the layer name.
# Function signature:
#   func(gdf: gpd.GeoDataFrame, path: str, uri: str, layer: str = None) -> gpd.GeoDataFrame
FILE_MIGRATION = None

# Schemas for the fields that are not defined in fiboa
# Keys must be the values from the COLUMNS dict, not the keys
MISSING_SCHEMAS = {

}


# Conversion function, usually no changes required
def convert(output_file, input_files = None, cache = None, source_coop_url = None, collection = False, compression = None):
    """
    Converts the field boundary datasets to fiboa.

    For reference, this is the order in which the conversion steps are applied:
    0. Read GeoDataFrame from file(s) / layer(s) and run the FILE_MIGRATION function if provided
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
        providers=PROVIDERS,
        source_coop_url=source_coop_url,
        extensions=EXTENSIONS,
        missing_schemas=MISSING_SCHEMAS,
        column_additions=ADD_COLUMNS,
        column_migrations=COLUMN_MIGRATIONS,
        column_filters=COLUMN_FILTERS,
        layer_filter=LAYER_FILTER,
        migration=MIGRATION,
        file_migration=FILE_MIGRATION,
        attribution=ATTRIBUTION,
        store_collection=collection,
        license=LICENSE,
        compression=compression,
    )
