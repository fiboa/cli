from .commons.ec import load_ec_mapping
from ..convert_utils import convert as convert_
import pandas as pd

SOURCES = {
    "http://epub.sjv.se/inspire/inspire/wfs?SERVICE=WFS%20&REQUEST=GetFeature%20&VERSION=1.0.0%20&TYPENAMES=inspire:arslager_skifte%20&outputFormat=shape-zip%20&CQL_FILTER=arslager=%272023%27%20%20and%20geom%20is%20not%20null%20&format_options=CHARSET:UTF-8": "se2023.zip"
}
ID = "se"
SHORT_NAME = "Sweden"
TITLE = "Swedish Crop Fields (Jordbruksskiften)"
DESCRIPTION = """
A crop field (Jordbruksskift) is a contiguous area of land within a block where a farmer grows a crop or otherwise manages the land.
To receive compensation for agricultural support (EU support), farmers apply for support from the
Swedish Agency for Agriculture via a SAM application. The data set contains parcels where the area
applied for and the area decided on are the same. The data is published at the end of a year.
"""
PROVIDERS = [
    {
        "name": "Jordbruksverket (The Swedish Board of Agriculture)",
        "url": "https://jordbruksverket.se/",
        "roles": ["producer", "licensor"]
    }
]
ATTRIBUTION = "Jordbruksverket"

LICENSE = "CC-0"  # "Open Data"
COLUMNS = {
    "geometry": "geometry",
    "id": "id",
    "faststalld": "area",
    "grdkod_mar": "crop_code",
    "crop_name": "crop_name",
}


MISSING_SCHEMAS = {
    "properties": {
        "crop_name": {
            "type": "string"
        },
        "crop_code": {
            "type": "string"
        },
    }
}


def convert(output_file, cache = None, mapping_file=None, **kwargs):
    ec_mapping = load_ec_mapping("se_2021.csv", url=mapping_file)
    original_name_mapping = {int(e["original_code"]): e["original_name"] for e in ec_mapping}

    def migrate(gdf):
        # Make year (1st january) from column "arslager"
        gdf['determination_datetime'] = pd.to_datetime(gdf['arslager'], format='%Y')
        gdf['id'] = gdf['blockid'] + "_" + gdf['skiftesbet']
        gdf['crop_name'] = gdf['grdkod_mar'].map(original_name_mapping)
        return gdf

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
        migration=migrate,
        attribution=ATTRIBUTION,
        license=LICENSE,
        **kwargs
    )
