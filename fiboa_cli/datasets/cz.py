from ..convert_utils import convert as convert_
import pandas as pd
from .commons.admin import add_admin

SOURCES = "https://mze.gov.cz/public/app/eagriapp/Files/geoprostor_zadosti23_2024-08-01_202409261243_epsg4258.zip"

ID = "cz"
SHORT_NAME = "Czech"
TITLE = "Field boundaries for Czech"
DESCRIPTION = "The cropfields of Czech (Plodina)"
PROVIDERS = [
    {
        "name": "Czech Ministry of Agriculture (Ministr Zemědělství)",
        "url": "https://mze.gov.cz/public/portal/mze/farmar/LPIS",
        "roles": ["producer", "licensor"]
    }
]
LICENSE = "CC-0"
COLUMNS = {
    'geometry': 'geometry',
    'ZAKRES_ID': 'id',
    'DPB_ID': 'block_id',
    'PLODINA_ID': 'crop_code',
    "PLOD_NAZE": "crop_name",
    "ZAKRES_VYM": "area",
    "DATUM_REP": "determination_datetime",
    # 'OKRES_NAZE': 'administrative_area_level_2'  # Region - District
}
COLUMN_MIGRATIONS = {
    'DATUM_REP': lambda col: pd.to_datetime(col, format="%d.%m.%Y")
}

MISSING_SCHEMAS = {
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

COLUMNS, ADD_COLUMNS, EXTENSIONS = add_admin(vars(), "CZ")

def convert(output_file, cache = None, **kwargs):
    convert_(
        output_file, cache, SOURCES,
        COLUMNS, ID, TITLE, DESCRIPTION,
        license=LICENSE,
        extensions=EXTENSIONS,
        column_additions=ADD_COLUMNS,
        missing_schemas=MISSING_SCHEMAS,
        column_migrations=COLUMN_MIGRATIONS,
        providers=PROVIDERS,
        **kwargs
    )
