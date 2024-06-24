from ..convert_utils import convert as convert_
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
    "KASVIKOODI": "crop_code",
    "KASVIKOODI_SELITE_FI": "crop_name",
}


def migrate(gdf):
    # Make year (1st january) from column "VUOSI"
    gdf['determination_datetime'] = pd.to_datetime(gdf['VUOSI'], format='%Y')
    gdf['geometry'] = gdf["geometry"].make_valid()
    gdf['area'] = np.where(gdf['PINTA_ALA'] == 0, gdf.area / 10000, gdf['PINTA_ALA'])
    return gdf


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

def convert(output_file, input_files = None, cache = None, source_coop_url = None, collection = False, compression = None):
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
        missing_schemas=MISSING_SCHEMAS,
        migration=migrate,
        attribution=ATTRIBUTION,
        store_collection=collection,
        license=LICENSE,
        compression=compression,
    )
