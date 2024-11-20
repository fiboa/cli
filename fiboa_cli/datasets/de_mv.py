from ..convert_utils import convert as convert_
from .commons.admin import add_admin

SOURCES = {
  "https://www.geodaten-mv.de/dienste/gdimv_feldblock_wfs?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&TYPENAME=mv:feldbloecke&OUTPUTFORMAT=shape-zip": "gdimv_feldblock_wfs.zip"
}

ID = "de_mv"
SHORT_NAME = "Germany, Mecklenburg-Western Pomerania"
TITLE = "Field boundaries for Mecklenburg-Western Pomerania, Germany"
DESCRIPTION = "Field block register of the Ministry of Agriculture and Environment M-V"

PROVIDERS = [
    {
        "name": "Ministerium für Landwirtschaft und Umwelt M-V",
        "url": "https://www.geodaten-mv.de/dienste/feldblock_atom?type=dataset&id=f18122c4-2585-4c22-9c48-9e960e8dhd34",
        "roles": ["producer", "licensor"]
    }
]
LICENSE = {
    "title": "No restrictions apply",
    "href": "https://www.geodaten-mv.de/dienste/feldblock_atom?type=dataset&id=f18122c4-2585-4c22-9c48-9e960e8dhd34",
    "type": "text/html",
    "rel": "license"
}

EXTENSIONS = [
    "https://fiboa.github.io/flik-extension/v0.1.0/schema.yaml"
]

COLUMNS = {
    'geometry': 'geometry',
    'fbid': ['id', 'flik'], # make flik id a dedicated column to align with NRW etc.
    'dgl_jahr': 'dgl_jahr',
    'bodennutzu': 'bodennutzu', # Bodennutzungsart
    'bez_kreis': 'bez_kreis', # Kreisbezeichnung
    'groesse_p': 'area', # Produktive Fläche des FB in Hektar (Nettofläche)
    'perimeter': 'perimeter', # Polygonumfang
    'erwind': 'erwind', # Gefährdungsklasse des Feldblockes gegenüber Winderosion nach DIN 19708
    'erwater': 'erwater', # Gefährdungsklasse des Feldblockes gegenüber Wassererosion nach DIN 19708
    'erwind_l': 'erwind_l',
    'erwater_l': 'erwater_l',
}
ISO_SCHEMA = {
    'type': 'string',
    'enum': [
        'Enat0', # keine bis sehr geringe Erosionsgefährdung
        'Enat0-EE',
        'Enat1', # sehr geringe Erosionsgefährdung
        'Enat1-EE',
        'Enat2', # geringe Erosionsgefährdung
        'Enat2-EE',
        'Enat3', # mittlere Erosionsgefährdung
        'Enat3-EE',
        'Enat4', # hohe Erosionsgefährdung
        'Enat4-EE',
        'Enat5', # sehr hohe Erosionsgefährdung
        'Enat5-EE',
        '-', # Keine Angabe
    ]
}
MISSING_SCHEMAS = {
    'properties': {
        'dgl_jahr': {
            'type': 'int16'
        },
        'bodennutzu': {
            'type': 'string',
            'enum': [
                'AAF', # Aufforstung auf Ackerfläche
                'AF', # Ackerfläche
                'AGL', # Aufforstung auf Grünland
                'AÖD', # Aufforstung auf Ödland
                'DK', # Dauerkultur
                'FO', # Forst
                'GL', # Grünland
            ]
        },
        'bez_kreis': {
            'type': 'string'
        },
        'erwind': {
            'type': 'string',
            'enum': [
                'CC0', # nicht relevant für Cross Compliance
                'CC1', # Erosionsgefährdung nach Direktzahlungen-Verpflichtungenverordnung
                '-', # keine Angabe
            ]
        },
        'erwater': {
            'type': 'string',
            'enum': [
                'CC0', # nicht relevant für Cross Compliance
                'CC1', # Erosionsgefährdung nach Direktzahlungen-Verpflichtungenverordnung (15-27,5 t/ha/a Bodenabtrag durch Wasser)
                'CC2', # hohe Erosionsgefährdung nach Direktzahlungen-Verpflichtungenverordnung (>27,5 t/ha/a Bodenabtrag durch Wasser)
                '-', # keine Angabe
            ]
        },
        'erwind_l': ISO_SCHEMA,
        'erwater_l': ISO_SCHEMA,
    }
}

COLUMNS, ADD_COLUMNS, EXTENSIONS = add_admin(vars(), "DE", "MV")

# Conversion function, usually no changes required
def convert(output_file, cache = None, **kwargs):
    convert_(
        output_file,
        cache,
        SOURCES,
        COLUMNS,
        ID,
        TITLE,
        DESCRIPTION,
        providers=PROVIDERS,
        extensions=EXTENSIONS,
        column_additions=ADD_COLUMNS,
        missing_schemas=MISSING_SCHEMAS,
        license=LICENSE,
        **kwargs
    )
