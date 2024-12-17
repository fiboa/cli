import re

import requests
from os import path
import pandas as pd

from .commons.data import read_data_csv
from ..convert_utils import convert as convert_
from .es import code_filter, ADD_COLUMNS, EXTENSIONS

# SOURCES = "https://filescartografia.navarra.es/2_CARTOGRAFIA_TEMATICA/2_6_SIGPAC/" # FULL Download timeout
ID = "es_na"
SHORT_NAME = "Spain Navarra"
TITLE = "Spain Navarra Crop fields"
DESCRIPTION = """
SIGPAC Crop fields of Spain - Navarra
"""
LICENSE = "CC-BY-4.0"  # https://sigpac.navarra.es/descargas/
ATTRIBUTION = "Comunidad Foral de Navarra"
PROVIDERS = [
    {
        "name": "Comunidad Foral de Navarra",
        "url": "https://gobiernoabierto.navarra.es/",
        "roles": ["producer", "licensor"]
    }
]
COLUMNS = {
    "geometry": "geometry",
    "BEGINLIFE": "determination_datetime",
    "crop:code": "IDUSO24",
    "crop:name": "crop:name",
    "crop:name_en": "crop:name_en",
}

COLUMN_MIGRATIONS = {
    "BEGINLIFE": lambda col: pd.to_datetime(col, format="%d/%m/%Y"),
}


def migrate(gdf):
    # This actually is a land use code. Not sure if we should put this in crop:code
    rows = read_data_csv("es_coda_uso.csv")
    mapping_en = {row["original_code"]: row["name_en"] for row in rows}
    gdf['crop:name'] = gdf['USO24']
    gdf['crop:name_en'] = gdf['IDUSO24'].map(mapping_en)
    return gdf


def convert(output_file, cache = None, **kwargs):
    # scrape HTML page for sources
    content = requests.get("https://sigpac.navarra.es/descargas/", verify=False).text
    base = re.search('var rutaBase = "(.*?)";', content).group(1)
    last = base.rsplit('/', 1)[-1]
    sources = {f"https://sigpac.navarra.es/descargas/{base}{src}.zip": [f"{last}{src}.shp"] for src in
               re.findall(r'value:"(\d+)"', content)}

    # Hostname has invalid SSL, hack around cache here
    assert cache, "This parser requires a cache. Use -c <cache_dir>"
    for s in list(sources):
        target = path.join(cache, s.rsplit("/", 1)[1])
        if not path.exists(target):
            r = requests.get(s, verify=False)
            if r.status_code == 200:
                with open(target, 'wb') as f:
                    f.write(r.content)
            else:
                sources.pop(s)

    convert_(
        output_file,
        cache,
        sources,
        COLUMNS,
        ID,
        TITLE,
        DESCRIPTION,
        extensions=EXTENSIONS,
        column_additions=ADD_COLUMNS,
        column_filters={"IDUSO24": code_filter},
        migration=migrate,
        providers=PROVIDERS,
        column_migrations=COLUMN_MIGRATIONS,
        attribution=ATTRIBUTION,
        license=LICENSE,
        index_as_id=True,
        **kwargs
    )
