from .commons.ec import ec_url
from ..convert_utils import BaseConverter
from .commons.admin import AdminConverterMixin
import pandas as pd
import numpy as np


class Converter(AdminConverterMixin, BaseConverter):
    sources = "https://download.inspire.ruokavirasto-awsa.com/data/2023/LandUse.ExistingLandUse.GSAAAgriculturalParcel.gpkg"
    id = "fi"
    short_name = "Finland"
    title = "Finnish Crop Fields (Maatalousmaa)"
    description = """
    The Finnish Food Authority (FFA) since 2020 produces spatial data sets,
    more specifically in this context the "Field parcel register" and "Agricultural parcel containing spatial data".
    A set called "Agricultural land: arable land, permanent grassland or permanent crop (land use)".
    """
    providers = [
        {
            "name": "Finnish Food Authority",
            "url": "https://www.ruokavirasto.fi/en/about-us/open-information/spatial-data-sets/",
            "roles": ["producer", "licensor"]
        }
    ]
    attribution = "Finnish Food Authority"
    license = "CC-BY-4.0"
    columns = {
        "geometry": "geometry",
        "PERUSLOHKOTUNNUS": "id",
        "LOHKONUMERO": "block_id",
        "area": "area",
        "VUOSI": "determination_datetime",
        "KASVIKOODI": "crop:code",
        "KASVIKOODI_SELITE_FI": "crop:name",
    }
    column_migrations = {
        # Make year (1st January) from column "VUOSI"
        "VUOSI": lambda col: pd.to_datetime(col, format='%Y'),
    }
    extensions = {"https://fiboa.github.io/crop-extension/v0.1.0/schema.yaml"}
    column_additions = {
        "crop:code_list": ec_url("fi_2020.csv")
    }

    def migrate(self, gdf):
        gdf['area'] = np.where(gdf['PINTA_ALA'] == 0, gdf.area / 10000, gdf['PINTA_ALA'])
        return gdf

    missing_schemas = {
        "properties": {
            "block_id": {
                "type": "int64"
            },
        }
    }
