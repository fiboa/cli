from ..convert_utils import convert as convert_
from .commons.admin import add_admin

import re

URL = "https://geoportal.saarland.de/gdi-sl/inspirewfs_Existierende_Bodennutzung_Antragsschlaege?SERVICE=WFS&REQUEST=GetFeature&VERSION=2.0.0&typeNames=elu:ExistingLandUseObject&outputFormat=application/gml%2Bxml;%20version=3.2&EPSG=4258&BBOX={bbox}"
BBOXES = [
    [49.1,6.5423790007724,49.332379000772,6.7747580015449],
    [49.1,6.7747580015449,49.332379000772,7.0071370023173],
    [49.1,7.0071370023173,49.216189500386,7.2395160030898],
    [49.216189500386,7.0071370023173,49.332379000772,7.2395160030898],
    [49.1,7.2395160030898,49.332379000772,7.4718950038622],
    [49.332379000772,6.31,49.564758001545,6.5423790007724],
    [49.332379000772,6.5423790007724,49.564758001545,6.6585685011587],
    [49.332379000772,6.6585685011587,49.564758001545,6.7747580015449],
    [49.332379000772,6.7747580015449,49.564758001545,6.8909475019311],
    [49.332379000772,6.8909475019311,49.564758001545,7.0071370023173],
    [49.332379000772,7.0071370023173,49.564758001545,7.1233265027036],
    [49.332379000772,7.1233265027036,49.564758001545,7.2395160030898],
    [49.332379000772,7.2395160030898,49.564758001545,7.4718950038622],
    [49.564758001545,6.7747580015449,49.797137002317,7.0071370023173],
    [49.564758001545,7.0071370023173,49.797137002317,7.2395160030898],
    [49.564758001545,7.2395160030898,49.797137002317,7.4718950038622],
]

SOURCES = {}
for i in range(1, len(BBOXES)):
    bbox_str = ",".join(map(str, BBOXES[i]))
    SOURCES[URL.format(bbox=bbox_str)] = "{i}.gml".format(i=i)

ID = "de_sl"
SHORT_NAME = "Germany, Saarland"
TITLE = "Field boundaries for Saarland, Germany"
DESCRIPTION = "This dataset contains data transformed into the INSPIRE data model “Land Use” of the IACS areas applied for within the framework of agricultural land promotion (GIS application) from the Saarland."
PROVIDERS = [
    {
        "name": "Ministerium für Umwelt, Klima, Mobilität, Agrar und Verbraucherschutz",
        "url": "https://geoportal.saarland.de",
        "roles": ["producer", "licensor"]
    }
]
ATTRIBUTION = "© GDI-SL 2024"
LICENSE = "cc-by-4.0"
EXTENSIONS = [
    "https://fiboa.github.io/flik-extension/v0.1.0/schema.yaml"
]

COLUMNS = {
    'geometry': 'geometry',
    'identifier': 'id',
    # 'observationDate': 'determination_datetime', # all values are null
    'flik': 'flik',
    'area': 'area',
    'name': 'name',
}

MISSING_SCHEMAS = {
    'properties': {
        'name': {
            'type': 'string'
        },
    }
}

def MIGRATION(gdf):
    gdf['flik'] = gdf['description'].apply(lambda x: parse_flik(x))
    gdf['area'] = gdf['description'].apply(lambda x: parse_size(x))
    return gdf

def parse_flik(x):
    match = re.search(r'flik:\s*([A-Z]{6}\d{10})', x, re.I)
    if match:
        return match.group(1)
    else:
        return None

def parse_size(x):
    match = re.search(r'Size in ha: (\d+(\.\d+)?)+', x, re.I)
    if match:
        return float(match.group(1))
    else:
        return None

COLUMNS, ADD_COLUMNS, EXTENSIONS = add_admin(vars(), "DE", "SL")

def convert(output_file, cache = None, **kwargs):
    convert_(
        output_file, cache,
        SOURCES, COLUMNS, ID, TITLE, DESCRIPTION,
        license=LICENSE,
        extensions=EXTENSIONS,
        migration=MIGRATION,
        column_additions=ADD_COLUMNS,
        missing_schemas=MISSING_SCHEMAS,
        attribution=ATTRIBUTION,
        providers=PROVIDERS,
        **kwargs
    )
