import pandas as pd

from ..convert_utils import convert as convert_
from .commons.ec import add_eurocrops

SOURCES = {"https://zenodo.org/records/8229128/files/LV_2021.zip": ["LV_2021/LV_2021_EC21.shp"]}

ID = "ec_lv"
SHORT_NAME = "Latvia"
TITLE = "Field boundaries for Latvia"
DESCRIPTION = "This dataset contains the field boundaries for all of Latvia in 2021. The data was collected by the Latvian government."

PROVIDERS = [
    {
        "name": "Lauku atbalsta dienests",
        "url": "https://www.lad.gov.lv/lv/lauku-registra-dati",
        "roles": ["producer", "licensor"],
    }
]
ATTRIBUTION = "Lauku atbalsta dienests"

COLUMNS = {
    "geometry": "geometry",
    "OBJECTID": "id",
    "AREA_DECLA": "area",
    "DATA_CHANG": "determination_datetime",
    "PERIOD_COD": "year",
    "PARCEL_ID": "parcel_id",
    "PRODUCT_CO": "crop_id",
    "AID_FORMS": "subsidy_type",
    "EC_NUTS3": "EC_NUTS3",
    #   'PRODUCT_DE': 'PRODUCT_DE',
}

COLUMN_MIGRATIONS = {
    "DATA_CHANG": lambda column: pd.to_datetime(column, format="%Y/%m/%d %H:%M:%S.%f", utc=True)
}

MISSING_SCHEMAS = {
    "required": [
        "year",
        "parcel_id",
        "crop_id",
        "subsidy_type",
        "EC_NUTS3",
        #       'PRODUCT_DE',
    ],
    "properties": {
        "year": {"type": "uint16", "minLength": 4, "maxLength": 4},
        "parcel_id": {"type": "uint64", "minLength": 8, "maxLength": 8},
        "crop_id": {"type": "uint16", "minLength": 3, "maxLength": 3},
        "subsidy_type": {"type": "string"},
        "EC_NUTS3": {
            "type": "string",
            "minLength": 5,
            "maxLength": 5,
            "pattern": "^[A-Z]{2}[0-9]{3}",
        },
        # 'PRODUCT_DE': {
        #     'type': 'string'
        # },
    },
}

ID, SHORT_NAME, TITLE, DESCRIPTION, PROVIDERS, EXTENSIONS, COLUMNS, LICENSE = add_eurocrops(
    vars(), 2021
)


def convert(output_file, cache=None, **kwargs):
    convert_(
        output_file,
        cache,
        SOURCES,
        COLUMNS,
        ID,
        TITLE,
        DESCRIPTION,
        column_migrations=COLUMN_MIGRATIONS,
        providers=PROVIDERS,
        extensions=EXTENSIONS,
        missing_schemas=MISSING_SCHEMAS,
        attribution=ATTRIBUTION,
        license=LICENSE,
        **kwargs,
    )
