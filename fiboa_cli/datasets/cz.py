import pandas as pd
from .commons.admin import AdminConverterMixin
from ..convert_utils import BaseConverter


class Converter(AdminConverterMixin, BaseConverter):
    sources = "https://mze.gov.cz/public/app/eagriapp/Files/geoprostor_zadosti23_2024-08-01_202409261243_epsg4258.zip"
    id = "cz"
    admin_country_code = "CZ"
    short_name = "Czech"
    title = "Field boundaries for Czech"
    description = "The cropfields of Czech (Plodina)"
    providers = [
        {
            "name": "Czech Ministry of Agriculture (Ministr Zemědělství)",
            "url": "https://mze.gov.cz/public/portal/mze/farmar/LPIS",
            "roles": ["producer", "licensor"]
        }
    ]
    license = "CC-0"
    columns = {
        'geometry': 'geometry',
        'ZAKRES_ID': 'id',
        'DPB_ID': 'block_id',
        'PLODINA_ID': 'crop_code',
        "PLOD_NAZE": "crop_name",
        "ZAKRES_VYM": "area",
        "DATUM_REP": "determination_datetime",
        # 'OKRES_NAZE': 'administrative_area_level_2'  # Region - District
    }
    column_migrations = {
        'DATUM_REP': lambda col: pd.to_datetime(col, format="%d.%m.%Y")
    }
    missing_schemas = {
        'properties': {
            'crop_code': {
                'type': 'string'
            },
            'crop_name': {
                'type': 'string'
            },
            'block_id': {
                'type': 'string'
            },
        }
    }
