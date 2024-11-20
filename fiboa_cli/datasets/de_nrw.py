from ..convert_utils import convert as convert_
from .commons.admin import add_admin

SOURCES = "https://www.opengeodata.nrw.de/produkte/umwelt_klima/bodennutzung/landwirtschaft/LFK-AKTI_EPSG25832_Shape.zip"
ID = "de_nrw"
SHORT_NAME = "Germany, North Rhine-Westphalia"
TITLE = "Field boundaries for North Rhine-Westphalia (NRW), Germany"
DESCRIPTION = """A field block (German: "Feldblock") is a contiguous agricultural area surrounded by permanent boundaries, which is cultivated by one or more farmers with one or more crops, is fully or partially set aside or is fully or partially taken out of production. Field blocks are classified separately according to the main land uses of arable land, grassland, permanent crops, 2nd pillar and other. Since 2005, field blocks in NRW have represented the area reference within the framework of the Integrated Administration and Control System (IACS) for EU agricultural subsidies."""
LICENSE = "dl-de/by-2-0"
PROVIDERS = [
    {
        "name": "Land Nordrhein-Westfalen / Open.NRW",
        "url": "https://www.opengeodata.nrw.de/produkte/umwelt_klima/bodennutzung/landwirtschaft/",
        "roles": ["producer", "licensor"]
    }
]
EXTENSIONS = [
    "https://fiboa.github.io/inspire-extension/v0.2.0/schema.yaml",
    "https://fiboa.github.io/flik-extension/v0.1.0/schema.yaml"
]
COLUMNS = {
    'geometry': 'geometry',
    'ID': 'id',
    'INSPIRE_ID': 'inspire:id',
    'FLIK': 'flik',
    'GUELT_VON': 'determination_datetime',
    'NUTZ_CODE': 'nutz_code',
    'NUTZ_TXT': 'nutz_txt',
    'AREA_HA': 'area'
}
MISSING_SCHEMAS = {
    'properties': {
        'nutz_code': {
            'type': 'string'
        },
        'nutz_txt': {
            'type': 'string'
        }
    }
}

COLUMNS, ADD_COLUMNS, EXTENSIONS = add_admin(vars(), "DE", "NW")

def convert(output_file, cache = None, **kwargs):
    convert_(
        output_file, cache,
        SOURCES, COLUMNS, ID, TITLE, DESCRIPTION,
        license=LICENSE,
        extensions=EXTENSIONS,
        column_additions=ADD_COLUMNS,
        missing_schemas=MISSING_SCHEMAS,
        providers=PROVIDERS,
        **kwargs
    )
