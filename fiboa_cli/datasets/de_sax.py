from ..convert_utils import convert as convert_
from .commons.admin import add_admin

import pandas as pd

SOURCES = {
  "https://www.smul.sachsen.de/gis-online/download/FBZ_ISS_Bereiche/gesamt_2024_RE.zip": [
    "2024_RE_FB_33.shp"
  ]
}
ID = "de_sax"
SHORT_NAME = "Germany, Saxony"
TITLE = "Field boundaries for Saxony, Germany"
DESCRIPTION = "Feldblöcke und förderfähige Elemente in Sachsen 2024"
PROVIDERS = [
    {
        "name": "Sächsisches Landesamt für Umwelt, Landwirtschaft und Geologie",
        "url": "https://geoportal.sachsen.de/",
        "roles": ["producer", "licensor"]
    }
]
ATTRIBUTION = "Sächsisches Landesamt für Umwelt, Landwirtschaft und Geologie"
LICENSE = "dl-de/by-2-0"
EXTENSIONS = [
    "https://fiboa.github.io/flik-extension/v0.1.0/schema.yaml"
]
COLUMNS = {
    'geometry': 'geometry',
    'FB_FLIK': ['id', 'flik'], # make flik id a dedicated column to align with NRW etc.
    'JAHR': 'determination_datetime',
    'FB_A_FLAE': 'area',
    # 'F_TYP': 'F_TYP', # all values 'FB'
    'FB_BN_KAT': 'FB_BN_KAT',
    'FB_BEZEICH': 'FB_BEZEICH',
    'ZUSTAENDIG': 'ZUSTAENDIG',
    'FB_FFH': 'FB_FFH',
    'FB_SPA': 'FB_SPA',
    'FB_NB': 'FB_NB',
    'NITRAT': 'NITRAT',
    'WT_WRRL': 'WT_WRRL',
    'NITRAT_TG': 'NITRAT_TG',
    'KWIND': 'KWIND',
    'KWASSER': 'KWASSER',
    'AGROFORST': 'AGROFORST',
    'AGRIPV': 'AGRIPV',
    'GLOEZ2': 'GLOEZ2',
    'OER_UNZUL': 'OER_UNZUL',
    'REG_SAAT': 'REG_SAAT',
    'BERG': 'BERG',
    # 'EA': 'EA', # all values null
}

MISSING_SCHEMAS = {
    'properties': {
        'FB_BN_KAT': {
            'type': 'string'
        },
        'FB_BEZEICH': {
            'type': 'string'
        },
        'ZUSTAENDIG': {
            'type': 'uint8'
        },
        'FB_FFH': {
            'type': 'boolean'
        },
        'FB_SPA': {
            'type': 'boolean'
        },
        'FB_NB': {
            'type': 'string'
        },
        'NITRAT': {
            'type': 'boolean'
        },
        'WT_WRRL': {
            'type': 'boolean'
        },
        'NITRAT_TG': {
            'type': 'boolean'
        },
        'KWIND': {
            'type': 'uint8'
        },
        'KWASSER': {
            'type': 'uint8'
        },
        'AGROFORST': {
            'type': 'boolean'
        },
        'AGRIPV': {
            'type': 'boolean'
        },
        'GLOEZ2': {
            'type': 'boolean'
        },
        'OER_UNZUL': {
            'type': 'string'
        },
        'REG_SAAT': {
            'type': 'string'
        },
        'BERG': {
            'type': 'uint8'
        },
    }
}

COLUMN_MIGRATIONS = {
    'JAHR': lambda col: pd.to_datetime(col, format='%Y')
}
for key in MISSING_SCHEMAS['properties']:
    schema = MISSING_SCHEMAS['properties'].get(key)
    if schema["type"] == "boolean":
        COLUMN_MIGRATIONS[key] = lambda col: col.map({'J': True, 'N': False}).astype(bool)

COLUMNS, ADD_COLUMNS, EXTENSIONS = add_admin(vars(), "DE", "SN")

def convert(output_file, cache = None, **kwargs):
    convert_(
        output_file, cache,
        SOURCES, COLUMNS, ID, TITLE, DESCRIPTION,
        license=LICENSE,
        extensions=EXTENSIONS,
        missing_schemas=MISSING_SCHEMAS,
        column_additions=ADD_COLUMNS,
        column_migrations=COLUMN_MIGRATIONS,
        attribution=ATTRIBUTION,
        providers=PROVIDERS,
        **kwargs
    )
