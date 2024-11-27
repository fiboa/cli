from ..convert_utils import convert as convert_
from .commons.admin import add_admin

SOURCES = {
  "https://data.geobasis-bb.de/geofachdaten/Landwirtschaft/dfbk.zip": ["DFBK_FB.shp"]
}
ID = "de_bb"
SHORT_NAME = "Germany, Berlin/Brandenburg"
TITLE = "Field boundaries for Berlin / Brandenburg, Germany"
DESCRIPTION = """A field block (German: "Feldblock") is a contiguous agricultural area surrounded by permanent boundaries, which is cultivated by one or more farmers with one or more crops, is fully or partially set aside or is fully or partially taken out of production."""
LICENSE = "dl-de/by-2-0"
PROVIDERS = [
    {
        "name": "Land Brandenburg",
        "url": "https://geobroker.geobasis-bb.de/gbss.php?MODE=GetProductInformation&PRODUCTID=9e95f21f-4ecf-4682-9a44-e5f7609f6fa0",
        "roles": ["producer", "licensor"]
    }
]
EXTENSIONS = [
    "https://fiboa.github.io/flik-extension/v0.1.0/schema.yaml"
]
COLUMNS = {
    'geometry': 'geometry',
    'FB_ID': ['flik', 'id'], # make flik id a dedicated column to align with NRW etc.
    'FGUE_JAHR': 'fgue_jahr',
    'FL_BRUTTO_': 'area',
    'FL_NETTO_H': 'net_area',
    'GUELTVON_F': 'determination_datetime',
    'GUELTBIS_F': 'expiry_datetime',
    'KREIS_NR': 'kreis_nr',
    'TK10_BLATT': "tk10",
    'HBN_KAT': 'hbn',
    'SHAPE_LEN': 'perimeter',
    # Don't include SHAPE_AREA
}
MISSING_SCHEMAS = {
    'properties': {
        'hbn': {
            'type': 'string'
        },
        'fgue_jahr': {
            'type': 'string'
        },
        'net_area': {
            'type': 'float',
            'exclusiveMinimum': 0
        },
        'expiry_datetime':  {
            'type': 'date-time'
        },
        'kreis_nr': {
            'type': 'uint16'
        },
        'tk10': {
            'type': 'string'
        }
    }
}

# todo: this includes Berlin, so we need to separate the subdivision code
COLUMNS, ADD_COLUMNS, EXTENSIONS = add_admin(vars(), "DE", "BB")

def convert(output_file, cache = None, **kwargs):
    convert_(
        output_file, cache,
        SOURCES, COLUMNS, ID, TITLE, DESCRIPTION,
        license=LICENSE,
        extensions=EXTENSIONS,
        column_additions=ADD_COLUMNS,
        missing_schemas=MISSING_SCHEMAS,
        providers=PROVIDERS,
        layer = "DFBK_FB",
        **kwargs
    )
