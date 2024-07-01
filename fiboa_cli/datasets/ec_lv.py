from ..convert_utils import convert as convert_

import pandas as pd

SOURCES = {
  "https://zenodo.org/records/8229128/files/LV_2021.zip": ["LV_2021/LV_2021_EC21.shp"]
}

ID = "ec_lv"
SHORT_NAME = "Latvia (Eurocrops, 2021)"
TITLE = "Field boundaries for Latvia from EuroCrops (2021)"
DESCRIPTION = """
This dataset contains the field boundaries for all of Latvia in 2021. The data was collected by the Latvian government and harmonized
by the EuroCrops project and is available on Zenodo.

EuroCrops is a dataset collection combining all publicly available self-declared crop reporting datasets from countries of the European Union.
The project is funded by the German Space Agency at DLR on behalf of the Federal Ministry for Economic Affairs and Climate Action (BMWK).
The work is licensed under a [Creative Commons Attribution-ShareAlike 4.0 International License][cc-by-sa].

The project developed a new **Hierarchical Crop and Agriculture Taxonomy (HCAT)** that harmonises all declared crops across the European Union.
In the data you'll find this as additional attributes:

- `EC_trans_n`: The original crop name translated into English
- `EC_hcat_n`: The machine-readable HCAT name of the crop
- `EC_hcat_c`: The 10-digit HCAT code indicating the hierarchy of the crop
"""

PROVIDERS = [
    {
        "name": "EuroCrops",
        "url": "https://github.com/maja601/EuroCrops/wiki/Latvia",
        "roles": ["producer", "licensor"]
    }
]
ATTRIBUTION = "Lauku atbalsta dienests"

LICENSE = "CC-BY-4.0"

COLUMNS = {
    'geometry': 'geometry', #fiboa core field
    'OBJECTID': 'id', #fiboa core field
    'AREA_DECLARED': 'area', #fiboa core field
    'DATA_CHANG': 'determination_datetime', #fiboa core field
    'PERIOD_CODE': 'year', #fiboa custom field
    'PARCEL_ID': 'parcel_id', #fiboa custom field
    'PRODUCT_CODE': 'crop_id', #fiboa custom field
    'AID_FORMS': 'subsidy_type', #fiboa custom field
    'EC_NUTS3': 'EC_NUTS3', #fiboa custom field
    'PRODUCT_DE': 'PRODUCT_DE', #fiboa custom field
    'EC_trans_n': 'EC_trans_n', #fiboa custom field
    'EC_hcat_n': 'EC_hcat_n', #fiboa custom field
    'EC_hcat_c': 'EC_hcat_c' #fiboa custom field
}

COLUMN_MIGRATIONS = {'DATA_CHANG': lambda column: pd.to_datetime(column, format = "%Y/%m/%d %H:%M:%S.%f", utc = True)}

MISSING_SCHEMAS = {
    'required': ['year', 'parcel_id', 'crop_id','subsidy_type', 'EC_NUTS3', 'PRODUCT_DE', 'EC_trans_n', 'EC_hcat_n', 'EC_hcat_c'],
    'properties': {
        'year': {
            'type': 'uint16',
            'minLength': 4,
            'maxLength': 4
        },
        'parcel_id': {
            'type': 'uint64',
            'minLength': 8,
            'maxLength': 8
        },
        'crop_id': {
            'type': 'uint16',
            'minLength': 3,
            'maxLength': 3
        },
        'subsidy_type': {
            'type': 'string'
        },
        'EC_NUTS3': {
            'type': 'string',
            'minLength': 5,
            'maxLength': 5,
            'pattern': '^[A-Z]{2}[0-9]{3}'
        },
        'PRODUCT_DE': {
            'type': 'string'
        },
        'EC_trans_n': {
            'type': 'string'
        },
        'EC_hcat_n': {
            'type': 'string'
        },
        'EC_hcat_c': {
            'type': 'uint32',
            'minLength': 10,
            'maxLength': 10
        }
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
        column_migrations=COLUMN_MIGRATIONS,
        providers=PROVIDERS,
        source_coop_url=source_coop_url,
        missing_schemas=MISSING_SCHEMAS,
        attribution=ATTRIBUTION,
        store_collection=collection,
        license=LICENSE,
        compression=compression,
    )
