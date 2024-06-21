from ..convert_utils import convert as convert_

SOURCES = "https://service.gdi-sh.de/SH_OpenGBD/feeds/Atom_SH_Feldblockfinder_OpenGBD/data/Feldbloecke_2024_GPKG.zip"
ID = "de_sh"
SHORT_NAME = "Germany, Schleswig-Holstein"
TITLE = "Field boundaries for Schleswig-Holstein (SH), Germany"
DESCRIPTION = """A field block (German: "Feldblock") is a contiguous agricultural area surrounded by permanent boundaries, which is cultivated by one or more farmers with one or more crops, is fully or partially set aside or is fully or partially taken out of production."""
PROVIDER_NAME = "Land Schleswig-Holstein"
PROVIDER_URL = "https://sh-mis.gdi-sh.de/catalog/#/datasets/iso/21f67269-780f-4f3c-8f66-03dde27acfe7"
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

def convert(output_file, input_files = None, cache = None, source_coop_url = None, collection = False, compression = None):
    """
    Converts the Schleswig-Holstein (Germany) field boundary datasets to fiboa.
    """
    convert_(
        output_file, cache,
        SOURCES, COLUMNS, ID, TITLE, DESCRIPTION,
        input_files=input_files,
        extensions=EXTENSIONS,
        missing_schemas=MISSING_SCHEMAS,
        license=LICENSE,
        source_coop_url=source_coop_url,
        provider_name=PROVIDER_NAME,
        provider_url=PROVIDER_URL,
        store_collection=collection,
        compression=compression,
    )
