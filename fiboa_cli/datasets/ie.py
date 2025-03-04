from .commons.admin import AdminConverterMixin
from ..convert_gml import gml_assure_columns
from ..convert_utils import BaseConverter
import geopandas as gpd


class IEConverter(AdminConverterMixin, BaseConverter):
    sources = {
      "https://osi-inspire-atom.s3-eu-west-1.amazonaws.com/IACSdata/IACS_GSAA_2022.zip": ["IACS_GSAA_2022.gml"]
    }

    id = "ie"
    short_name = "Ireland"
    title = "Ireland INSPIRE Geospatial aid application (GSAA) dataset"
    description = """
    This data represents the outline shape of LPIS parcels as claimed under area based schemes. The dataset includes the crops claimed as part of the annual GSAA.
    Yearly information provided through the beneficiary declaration.
    """

    providers = [
        {
            "name": "Ireland Department of Agriculture, Food and the Marine",
            "url": "https://inspire.geohive.ie/geoportal/",
            "roles": ['producer', 'licensor']
        }
    ]
    attribution = "Ireland Department of Agriculture, Food and the Marine"
    license = "CC-BY-4.0"
    columns = {
        "geometry": "geometry",
        "crop_name": "crop_name",
        "localId": "id",
        "determination_datetime": "determination_datetime",
    }
    # TODO use crop-extension, maybe with reverse mapping

    missing_schemas = {
        "properties": {
            "crop_name": {
                "type": "string"
            },
        }
    }

    def migrate(self, gdf) -> gpd.GeoDataFrame:
        # crop_name can be multiple: "crop1, crop2, crop3". We only read the main crop (first).
        gdf['crop_name'] = gdf['crop_name'].str.split(', ').str.get(0)
        gdf = gdf[gdf['crop_name'] != 'Void']  # Exclude non-agriculture fields
        gdf["determination_datetime"] = gdf["observationDate"].str.replace("+01:00", "T00:00:00Z")
        return gdf

    def file_migration(self, gdf: gpd.GeoDataFrame, path: str, uri: str, layer: str = None) -> gpd.GeoDataFrame:
        return gml_assure_columns(gdf, path, uri, layer,
                                  crop_name={"ElementPath": "specificLandUse@title", "Type": "String", "Width": 255})

    def layer_filter(self, layer: str, uri: str) -> bool:
        return layer == "ExistingLandUseObject"
