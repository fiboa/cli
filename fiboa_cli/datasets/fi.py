from ..convert_utils import convert as convert_
from .commons.admin import add_admin
import pandas as pd
import numpy as np

SOURCES = "https://download.inspire.ruokavirasto-awsa.com/data/2023/LandUse.ExistingLandUse.GSAAAgriculturalParcel.gpkg"
ID = "fi"
SHORT_NAME = "Finland"
TITLE = "Finnish Crop Fields (Maatalousmaa)"
DESCRIPTION = """
The Finnish Food Authority (FFA) since 2020 produces spatial data sets,
more specifically in this context the "Field parcel register" and "Agricultural parcel containing spatial data".
A set called "Agricultural land: arable land, permanent grassland or permanent crop (land use)".
"""
PROVIDERS = [
    {
        "name": "Finnish Food Authority",
        "url": "https://www.ruokavirasto.fi/en/about-us/open-information/spatial-data-sets/",
        "roles": ["producer", "licensor"]
    }
]
ATTRIBUTION = "Finnish Food Authority"

LICENSE = "CC-BY-4.0"
COLUMNS = {
    "geometry": "geometry",
    "PERUSLOHKOTUNNUS": "id",
    "LOHKONUMERO": "block_id",
    "area": "area",
    "VUOSI": "determination_datetime",
    "KASVIKOODI": "crop_code",
    "KASVIKOODI_SELITE_FI": "crop_name",
}
COLUMN_MIGRATIONS = {
    # Make year (1st january) from column "VUOSI"
    "VUOSI": lambda col: pd.to_datetime(col, format='%Y'),
}

def migrate(gdf):
    gdf['area'] = np.where(gdf['PINTA_ALA'] == 0, gdf.area / 10000, gdf['PINTA_ALA'])
    return gdf

COLUMNS, ADD_COLUMNS, EXTENSIONS = add_admin(vars(), "FI")

MISSING_SCHEMAS = {
    "properties": {
        "block_id": {
            "type": "int64"
        },
        "crop_name": {
            "type": "string"
        },
        "crop_code": {
            "type": "string"
        },
    }
}

def convert(output_file, cache = None, **kwargs):
    convert_(
        output_file,
        cache,
        SOURCES,
        COLUMNS,
        ID,
        TITLE,
        DESCRIPTION,
        providers=PROVIDERS,
        missing_schemas=MISSING_SCHEMAS,
        extensions=EXTENSIONS,
        column_additions=ADD_COLUMNS,
        column_migrations=COLUMN_MIGRATIONS,
        migration=migrate,
        attribution=ATTRIBUTION,
        license=LICENSE,
        **kwargs
    )
