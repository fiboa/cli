# TEMPLATE FOR A FIBOA CONVERTER
#
# Copy this file and rename it to something sensible.
# The name of the file will be the name of the converter in the cli.
# If you name it 'de_abc' you'll be able to run `fiboa convert de_abc` in the cli.

from ..convert_utils import BaseConverter


class TemplateConverter(BaseConverter):  # change this class name to your use case
    # File(s) to read the data from, usually publicly accessible URLs.
    # Can read any (zipped) tabular data format that GeoPandas can read through read_file() or read_parquet().
    # Supported protocols: HTTP(S), GCS, S3, or the local file system
    #
    # Multiple options are possible:
    # 1. a single URL (filename must be in the URL). The file is read as is.
    sources = "https://fiboa.example/file.xyz"

    # 2. a dictionary with a mapping of URLs (where the filename can't necessarily be determined from the URL) to filenames.
    # sources = {
    #   "https://fiboa.example/archive/758?download=1": "us.gpkg"
    #   "https://fiboa.example/archive/355?download=1": "canada.gpkg"
    # }
    # 3. a dictionary with a mapping of URLs to a list of filenames in ZIP ot 7Z files to read from.
    # sources = {
    #   "https://fiboa.example/north_america.zip": ["us.gpkg", "canaga.gpkg"]
    # }

    # If multiple years are available, you can replace sources by years.
    # The dict-key can be used on the cli command line, the value will be used as 'sources'
    #
    # years = {
    #    2023: "https://fiboa.example/file_2023.xyz"
    #    2024: "https://fiboa.example/file_2023.xyz"
    # }

    # Override filter function for the layer in the file(s) to read.
    # def layer_filter(self, layer: str, uri: str) -> bool:
    #     return True

    # Unique identifier for the collection
    id = "abc"
    # Geonames for the data (e.g. Country, Region, Source, Year)
    short_name = "Country, Region, etc."
    # Title of the collection
    title = "Field boundaries for Country, Region, etc."
    # Description of the collection. Can be multiline and include CommonMark.
    description = """Describe the dataset here."""

    # A list of providers that contributed to the data.
    # This should be an array of Provider Objects:
    # https://github.com/radiantearth/stac-spec/blob/master/collection-spec/collection-spec.md#provider-object
    providers = [
        {
            "name": "ABC Corp",
            "url": "https://abc.example",
            "roles": ["producer", "licensor"]
        }
    ]

    # Attribution (e.g. copyright or citation statement as requested by provider).
    # The attribution is usually shown on the map, in the lower right corner.
    # Can be None if not applicable
    attribution = "© 2024 ABC Corp."

    # License of the data, either
    # 1. a SPDX license identifier (including "dl-de/by-2-0" / "dl-de/zero-2-0"), or
    license = "CC-BY-4.0"
    # 2. a STAC Link Object with relation type "license"
    # license = {"title": "CC-BY-4.0", "href": "https://creativecommons.org/licenses/by/4.0/", "type": "text/html", "rel": "license"}

    # Map original column names to fiboa property names
    # You also need to list any column that you may have added in the MIGRATION function (see below).
    # GeoJSON: Nested objects can be accessed using a dot, e.g. "area.value" for {"area": {"value": 123}}
    columns = {
        "area_m": "area"
    }

    # Add columns with constant values.
    # The key is the column name, the value is a constant value that's used for all rows.
    column_additions = {
    }

    # A list of implemented extension identifiers
    extensions = set()

    # Functions to migrate data in columns to match the fiboa specification.
    # Example: You have a column area_m in square meters and want to convert
    # to hectares as required for the area field in fiboa.
    # Function signature:
    #   func(column: pd.Series) -> pd.Series
    column_migrations = {
        "area_m": lambda column: column * 0.0001
    }

    # Filter columns to only include the ones that are relevant for the collection,
    # e.g. only rows that contain the word "agriculture" but not "forest" in the column "land_cover_type".
    # Lamda function accepts a Pandas Series and returns a Series or a Tuple with a Series and True to inverse the mask.
    column_filters = {
        "land_cover_type": lambda col: (col.isin(["agrictulture"]), True)
    }

    # Override to migrate the full GeoDataFrame if the other options are not sufficient
    # This should be the last resort!
    # def migrate(self, gdf) -> gpd.GeoDataFrame:
    #     return gdf

    # Custom function to execute actions on the the GeoDataFrame that are loaded from individual file or layers.
    # This is useful if the data is split into multiple files/layers and columns should be added or changed
    # on a per-file/layer basis for example.
    # The path contains the local path to the file that was read.
    # The uri contains the URL that was read.
    # The layer may contain the layer name.
    # def file_migration(self, gdf: gpd.GeoDataFrame, path: str, uri: str, layer: str = None) -> gpd.GeoDataFrame:
    #     return data

    # Schemas for the fields that are not defined in fiboa
    # Keys must be the values from the COLUMNS dict, not the keys
    missing_schemas = {
        "required": ["my_id"], # i.e. non-nullable properties
        "properties": {
            "my_id": {
                "type": "string"
            }
        }
    }

    """
    def convert(self, *args, **kwargs):
    Converts the field boundary datasets to fiboa.

    For reference, this is the order in which the conversion steps are applied:
    0. Read GeoDataFrame from file(s) / layer(s) and run self.file_migration()
    1. Run global migration self.migrate()
    2. Run filters to remove rows that shall not be in the final data
       (if provided through self.column_filters)
    3. Add columns with constant values
    4. Run column migrations (if provided through self.column_migrations)
    5. Duplicate columns (if an array is provided as the value in self.columns)
    6. Rename columns (as provided in self.columns)
    7. Remove columns (if column is not present as value in self.columns)
    8. Create the collection
    9. Change data types of the columns based on the provided schemas
    (fiboa spec, extensions, and self.missing_schemas)
    10. Write the data to the Parquet file
    """
