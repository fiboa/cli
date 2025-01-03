from os.path import join, dirname

from .commons.ec import load_ec_mapping
from ..util import log
from ..convert_utils import convert as convert_
import pandas as pd


SOURCES = {
    "https://www.nass.usda.gov/Research_and_Science/Crop-Sequence-Boundaries/datasets/NationalCSB_2016-2023_rev23.zip": ["NationalCSB_2016-2023_rev23/CSB1623.gdb"]
}
ID = "us_usda_cropland"
SHORT_NAME = "US (USDA CSB)"
TITLE = "U.S. Department of Agriculture Crop Sequence Boundaries"
DESCRIPTION = """
The Crop Sequence Boundaries (CSB) developed with USDA's Economic Research Service, produces estimates of field boundaries, crop acreage, and crop rotations across the contiguous United States. It uses satellite imagery with other public data and is open source allowing users to conduct area and statistical analysis of planted U.S. commodities and provides insight on farmer cropping decisions.

NASS needed a representative field to predict crop planting based on common crop rotations such as corn-soy and ERS is using this product to study changes in farm management practices like tillage or cover cropping over time.

CSB represents non-confidential single crop field boundaries over a set time frame. It does not contain personal identifying information. The boundaries captured are of crops grown only, not ownership boundaries or tax parcels (unit of property). The data are from satellite imagery and publicly available data, it does not come from producers or agencies like the Farm Service Agency.
"""

EXTENSIONS = ["https://fiboa.github.io/crop-extension/v0.1.0/schema.yaml"]
PROVIDERS = [
    {
        "name": "United States Department of Agriculture",
        "url": "https://www.nass.usda.gov/",
        "roles": ["licensor", "producer"]
    }
]
LICENSE ={
    "title": "License and Liability",
    "href": "https://gee-community-catalog.org/projects/csb/#license-and-liability",
    "type": "text/html",
    "rel": "license"
}

COLUMNS = {
    "geometry": "geometry",
    "CSBID": "id",
    'CDL2023': 'crop:code',
    'crop:name': 'crop:name',
    'CNTY': "administrative_area_level_2",
}

ADD_COLUMNS = {
    "determination_datetime": "2023-05-01T00:00:00Z",
    "crop:code_list": "https://fiboa.org/code/us/usda/crop.csv",
}

MISSING_SCHEMAS = {
    "properties": {
        "administrative_area_level_2": {
            "type": "string"
        },
    }
}


def migrate(gdf):
    # "dissolve": merge adjacent polygons with the same crop
    # geodataframe.Dissolve(method="unary") is **slow** for large datasets
    # So we're handling this huge dataset in blocks, states are a natural grouping-method
    states = list(gdf["STATEFIPS"].unique())
    gdfs = []
    for state in states:
        log(f"Handling State {state}", "info")
        df = gdf[gdf["STATEFIPS"] == state].explode()
        df.dissolve(by=["CDL2023"], aggfunc="first").explode()
        gdfs.append(df)
    gdf = pd.concat(gdfs)
    del gdfs
    mapping = load_ec_mapping(url=join(dirname(__file__), "data-files", "us_usda_cropland.csv"))
    original_name_mapping = {int(e["original_code"]): e["original_name"] for e in mapping}
    gdf['crop:name'] = gdf['CDL2023'].map(original_name_mapping)
    return gdf


def convert(output_file, cache = None, **kwargs):
    convert_(
        output_file,
        cache,
        SOURCES,
        COLUMNS,
        ID,
        TITLE,
        DESCRIPTION,
        migration=migrate,
        column_additions=ADD_COLUMNS,
        extensions=EXTENSIONS,
        providers=PROVIDERS,
        license=LICENSE,
        missing_schemas=MISSING_SCHEMAS,
        **kwargs
    )
