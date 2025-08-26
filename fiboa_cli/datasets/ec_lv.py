import pandas as pd

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import EuroCropsConverterMixin


class Converter(EuroCropsConverterMixin, FiboaBaseConverter):
    ec_mapping_csv = "lv_2021.csv"
    ec_year = 2021
    sources = {"https://zenodo.org/records/8229128/files/LV_2021.zip": ["LV_2021/LV_2021_EC21.shp"]}
    id = "ec_lv"
    short_name = "Latvia"
    title = "Field boundaries for Latvia"
    description = "This dataset contains the field boundaries for all of Latvia in 2021. The data was collected by the Latvian government."

    providers = [
        {
            "name": "Lauku atbalsta dienests",
            "url": "https://www.lad.gov.lv/lv/lauku-registra-dati",
            "roles": ["producer", "licensor"],
        }
    ]
    attribution = "Lauku atbalsta dienests"

    columns = {
        "geometry": "geometry",
        "OBJECTID": "id",
        "AREA_DECLA": "metrics:area",
        "DATA_CHANG": "determination:datetime",
        "PERIOD_COD": "year",
        "PARCEL_ID": "parcel_id",
        "PRODUCT_CO": "crop:code",
        "AID_FORMS": "subsidy_type",
        "EC_NUTS3": "EC_NUTS3",  # should this be HCAT?
        #   'PRODUCT_DE': 'PRODUCT_DE',
    }

    column_migrations = {
        "DATA_CHANG": lambda column: pd.to_datetime(column, format="%Y/%m/%d %H:%M:%S.%f", utc=True)
    }

    missing_schemas = {
        "required": [
            "year",
            "parcel_id",
            "crop:code",
            "subsidy_type",
            "EC_NUTS3",
            #       'PRODUCT_DE',
        ],
        "properties": {
            "year": {"type": "uint16", "minLength": 4, "maxLength": 4},
            "parcel_id": {"type": "uint64", "minLength": 8, "maxLength": 8},
            "crop:code": {"type": "uint16", "minLength": 3, "maxLength": 3},
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

    def add_hcat(self, gdf):
        # skip adding hcat
        return gdf
