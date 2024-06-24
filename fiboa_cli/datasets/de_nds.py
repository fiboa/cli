from ..convert_utils import convert as convert_

SOURCES = "https://sla.niedersachsen.de/mapbender_sla/download/FB_NDS.zip"
ID = "de_nds"
SHORT_NAME = "Germany, Lower Saxony"
TITLE = "Field boundaries for Lower Saxony, Germany"
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

def convert(output_file, input_files = None, cache = None, source_coop_url = None, collection = False, compression = None):
    """
    Converts the Lower Saxony (Germany) field boundary datasets to fiboa.
    """
    convert_(
        output_file, cache,
        SOURCES, COLUMNS, ID, TITLE, DESCRIPTION,
        input_files=input_files,
        license=LICENSE,
        extensions=EXTENSIONS,
        missing_schemas=MISSING_SCHEMAS,
        attribution=ATTRIBUTION,
        source_coop_url=source_coop_url,
        providers=PROVIDERS,
        store_collection=collection,
        compression=compression,
    )
