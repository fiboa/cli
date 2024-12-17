from .commons.data import read_data_csv
from ..convert_utils import convert as convert_
from .es import ADD_COLUMNS, EXTENSIONS, code_filter
import pandas as pd


# https://idearagon.aragon.es/descargas
# These files can be annoying to download (web server failure, no http-range support for continuation)
# Alternative is to download the files by municipality, check the atom.xml
SOURCES = {
    "https://icearagon.aragon.es/datosdescarga/descarga.php?file=/CartoTema/sigpac/rec22_sigpac.shp.zip&blocksize=0": "rec22_sigpac.shp.zip",
    "https://icearagon.aragon.es/datosdescarga/descarga.php?file=/CartoTema/sigpac/rec44_sigpac.shp.zip&blocksize=0": "rec44_sigpac.shp.zip",
    "https://icearagon.aragon.es/datosdescarga/descarga.php?file=/CartoTema/sigpac/rec50_sigpac.shp.zip&blocksize=0": "rec50_sigpac.shp.zip",
}

ID = "es_ar"
SHORT_NAME = "Spain Aragon"
TITLE = "Spain Aragon Crop fields"
DESCRIPTION = """
SIGPAC - Sistema de Información Geográfica de la Política Agrícola común (ejercicio actual)

Crop Fields of Spain province Aragon
"""
PROVIDERS = [
    {
        "name": "Gobierno de Aragon",
        "url": "https://www.aragon.es/",
        "roles": ["producer", "licensor"]
    }
]

# License: https://idearagon.aragon.es/portal/politica-privacidad.jsp
LICENSE = "CC-BY-4.0"
ATTRIBUTION = "(c) Gobierno de Aragon"
COLUMNS = {
    "geometry": "geometry",
    "dn_oid": "id",
    "provincia": "admin_province_code",
    "municipio": "admin_municipality_code",
    "uso_sigpac": "crop:code",
    "crop:name": "crop:name",
    "crop:name_en": "crop:name_en",
    "ejercicio": "determination_datetime"
}

def migrate(gdf):
    # This actually is a land use code. Not sure if we should put this in crop:code
    rows = read_data_csv("es_coda_uso.csv")
    mapping = {row["original_code"]: row["original_name"] for row in rows}
    mapping_en = {row["original_code"]: row["name_en"] for row in rows}
    gdf['crop:name'] = gdf['uso_sigpac'].map(mapping)
    gdf['crop:name_en'] = gdf['uso_sigpac'].map(mapping_en)
    return gdf


COLUMN_MIGRATIONS = {
    "ejercicio": lambda col: pd.to_datetime(col, format='%Y'),
}

ADD_COLUMNS = ADD_COLUMNS | {
    "admin:country_code": "ES",
    "admin:subdivision_code": "AR"
}

MISSING_SCHEMAS = {
    "properties": {
        "admin_province_code": {
            "type": "string"
        },
        "admin_municipality_code": {
            "type": "string"
        },
    }
}

EXTENSIONS = EXTENSIONS + ['https://fiboa.github.io/administrative-division-extension/v0.1.0/schema.yaml']


def convert(output_file, cache = None, **kwargs):
    convert_(
        output_file,
        cache,
        SOURCES,
        COLUMNS,
        ID,
        TITLE,
        DESCRIPTION,
        migration=migrate,
        column_additions=ADD_COLUMNS,
        column_migrations=COLUMN_MIGRATIONS,
        extensions=EXTENSIONS,
        providers=PROVIDERS,
        missing_schemas=MISSING_SCHEMAS,
        attribution=ATTRIBUTION,
        license=LICENSE,
        column_filters={"uso_sigpac": code_filter},
        **kwargs
    )
