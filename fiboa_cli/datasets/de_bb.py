from ..convert_utils import convert as convert_

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

def convert(output_file, input_files = None, cache = None, source_coop_url = None, collection = False, compression = None):
    """
    Converts the Berlin/Brandenburg (Germany) field boundary datasets to fiboa.
    """
    convert_(
        output_file, cache,
        SOURCES, COLUMNS, ID, TITLE, DESCRIPTION,
        input_files=input_files,
        license=LICENSE,
        extensions=EXTENSIONS,
        missing_schemas=MISSING_SCHEMAS,
        source_coop_url=source_coop_url,
        providers=PROVIDERS,
        store_collection=collection,
        layer = "DFBK_FB",
        compression=compression,
    )
