from ..convert_utils import convert as convert_
from .commons.admin import add_admin

SOURCES = "https://sla.niedersachsen.de/mapbender_sla/download/FB_NDS.zip"
ID = "de_nds"
SHORT_NAME = "Germany, Lower Saxony/Bremen/Hamburg"
TITLE = "Field boundaries for Lower Saxony / Bremen / Hamburg, Germany"
DESCRIPTION = """A field block (German: "Feldblock") is a contiguous agricultural area surrounded by permanent boundaries, which is cultivated by one or more farmers with one or more crops, is fully or partially set aside or is fully or partially taken out of production."""
PROVIDERS = [
    {
        "name": "ML/SLA Niedersachsen",
        "url": "https://sla.niedersachsen.de/landentwicklung/LEA/",
        "roles": ["producer", "licensor"]
    }
]
ATTRIBUTION = "© ML/SLA Niedersachsen (2024), dl-de/by-2-0 (www.govdata.de/dl-de/by-2-0), Daten bearbeitet"
LICENSE = "dl-de/by-2-0"
EXTENSIONS = [
    "https://fiboa.github.io/flik-extension/v0.1.0/schema.yaml"
]
COLUMNS = {
    'geometry': 'geometry',
    'FLIK': ['id', 'flik'], # make flik id a dedicated column to align with NRW etc.
    'STAND': 'determination_datetime',
    'ANT_JAHR': 'ant_jahr',
    'BNK': 'bnk',
    'BNK_TXT': 'bnk_txt',
    'FLAECHE': 'area',
    'SHAPE_Leng': "perimeter"
    # Don't include SHAPE_Area
}
MISSING_SCHEMAS = {
    'properties': {
        'ant_jahr': {
            'type': 'int16'
        },
        'bnk': {
            'type': 'string'
        },
        'bnk_txt': {
            'type': 'string'
        }
    }
}

# todo: this includes Hamburg and Bremen, so we need to separate the subdivision code
COLUMNS, ADD_COLUMNS, EXTENSIONS = add_admin(vars(), "DE", "NI")

def convert(output_file, cache = None, **kwargs):
    convert_(
        output_file, cache,
        SOURCES, COLUMNS, ID, TITLE, DESCRIPTION,
        license=LICENSE,
        extensions=EXTENSIONS,
        column_additions=ADD_COLUMNS,
        missing_schemas=MISSING_SCHEMAS,
        attribution=ATTRIBUTION,
        providers=PROVIDERS,
        **kwargs
    )
