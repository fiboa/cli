from ..convert_utils import convert as convert_
from .commons.admin import add_admin


SOURCES = "https://service.gdi-sh.de/SH_OpenGBD/feeds/Atom_SH_Feldblockfinder_OpenGBD/data/Feldbloecke_2024_GPKG.zip"
ID = "de_sh"
SHORT_NAME = "Germany, Schleswig-Holstein"
TITLE = "Field boundaries for Schleswig-Holstein (SH), Germany"
DESCRIPTION = """A field block (German: "Feldblock") is a contiguous agricultural area surrounded by permanent boundaries, which is cultivated by one or more farmers with one or more crops, is fully or partially set aside or is fully or partially taken out of production."""
PROVIDERS = [
    {
        "name": "Land Schleswig-Holstein",
        "url": "https://sh-mis.gdi-sh.de/catalog/#/datasets/iso/21f67269-780f-4f3c-8f66-03dde27acfe7",
        "roles": ["producer", "licensor"]
    }
]
LICENSE = "dl-de/zero-2-0"
EXTENSIONS = [
    "https://fiboa.github.io/flik-extension/v0.1.0/schema.yaml"
]
COLUMNS = {
    'geometry': 'geometry',
    'fachguelti': 'determination_datetime',
    'FLIK': ['flik', 'id'], # make flik id a dedicated column to align with NRW etc.
    'Flaeche': 'area',
    'HBN': 'hbn'
}
MISSING_SCHEMAS = {
    'properties': {
        'hbn': {
            'type': 'string'
        }
    }
}

COLUMNS, ADD_COLUMNS, EXTENSIONS = add_admin(vars(), "DE", "SH")

def convert(output_file, cache = None, **kwargs):
    convert_(
        output_file, cache,
        SOURCES, COLUMNS, ID, TITLE, DESCRIPTION,
        extensions=EXTENSIONS,
        column_additions=ADD_COLUMNS,
        missing_schemas=MISSING_SCHEMAS,
        license=LICENSE,
        providers=PROVIDERS,
        **kwargs
    )
