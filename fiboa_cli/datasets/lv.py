from .commons.ec import load_ec_mapping
from ..convert_utils import convert as convert_
import numpy as np

SOURCES = "https://karte.lad.gov.lv/arcgis/services/lauki/MapServer/WFSServer"
ID = "lv"
SHORT_NAME = "Latvia"
TITLE = "Latvia Lauki Parcels"
DESCRIPTION = """
Latvia offers parcel data on a [public map, available to any user](https://www.lad.gov.lv/lv/lauku-registra-dati).

The land register is a geographic information system (GIS) that gathers information about agricultural land that is
eligible for state and European Union support from direct support scheme payments or environmental,
climate and rural landscape improvement payments.

The GIS of the field register contains a database of field blocks with interconnected spatial cartographic
data and information of attributes subordinate to them: geographic attachment, identification numbers
and area information.

Relevant datasets are; Country blocks (Lauku Bloki), Fields (Lauki) and Landscape elements.
"""
EXTENSIONS = ["https://fiboa.github.io/crop-extension/v0.1.0/schema.yaml"]
PROVIDERS = [
    {
        "name": "Rural Support Service Republic of Latvia (Lauku atbalsta dienests)",
        "url": "https://www.lad.gov.lv/lv/lauku-registra-dati",
        "roles": ["licensor", "producer"]
    }
]
ATTRIBUTION = "Lauku atbalsta dienests"
LICENSE = "CC-BY-SA-4.0"  # Not sure, taken from Eurocrops. It is "public" and free and "available to any user"

COLUMNS = {
    "OBJECTID": "id",
    'PARCEL_ID': 'parcel_id',
    "geometry": "geometry",
    "DATA_CHANGED_DATE": "determination_datetime",
    "area": "area",
    "crop:code_list": "crop:code_list",
    "PRODUCT_CODE": "crop:code",
    "crop:name": "crop:name",
    "crop:name_en": "crop:name_en",
}
MISSING_SCHEMAS = {
    'properties': {
        'parcel_id': {
            'type': 'uint64',
        }
    }
}


def convert(output_file, cache = None, mapping_file = None, **kwargs):
    count = 3000
    sources = {
        f"{SOURCES}?request=GetFeature&service=wfs&version=2.0.0&typeNames=Lauki&count={count}&startindex={count * i}": f"lv_{i}_{count}.xml"
        for i in range(500000 // count)  # TODO number should be dynamic, stop reading with 0 results
    }

    ec_mapping = load_ec_mapping("lv_2021.csv", url=mapping_file)
    original_name_mapping = {int(e["original_code"]): e["original_name"] for e in ec_mapping}
    name_mapping = {int(e["original_code"]): e["translated_name"] for e in ec_mapping}

    def migrate(gdf):
        gdf['area'] = np.where(gdf['AREA_DECLARED'] == 0, gdf.area / 10000, gdf['AREA_DECLARED'])
        gdf["crop:code_list"] = f"https://raw.githubusercontent.com/maja601/EuroCrops/refs/heads/main/csvs/country_mappings/lv_2021.csv"
        gdf['crop:name'] = gdf['PRODUCT_CODE'].map(original_name_mapping)
        gdf['crop:name_en'] = gdf['PRODUCT_CODE'].map(name_mapping)
        return gdf

    convert_(
        output_file,
        cache,
        sources,
        COLUMNS,
        ID,
        TITLE,
        DESCRIPTION,
        missing_schemas=MISSING_SCHEMAS,
        extensions=EXTENSIONS,
        migration=migrate,
        providers=PROVIDERS,
        attribution=ATTRIBUTION,
        license=LICENSE,
        **kwargs
    )
