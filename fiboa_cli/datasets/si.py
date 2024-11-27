from ..convert_utils import convert as convert_
from .commons.admin import add_admin

SOURCES = {
    "https://rkg.gov.si/razno/portal_analysis/KMRS_2023.rar": ["KMRS_2023.shp"]
}
ID = "si"
SHORT_NAME = "Slovenia"
TITLE = "Slovenia Crop Fields"
DESCRIPTION = """
The Slovenian government provides slightly different, relevant open data sets called GERK, KMRS, RABA and EKRZ.
This converter uses the KRMS dataset, which includes CAP applications of the last year and discerns
around 150 different crop categories.
"""
PROVIDERS = [
    {
        "name": "Ministry of Agriculture, Forestry and Food (Ministrstvo za kmetijstvo, gozdarstvo in prehrano)",
        "url": "https://www.gov.si/drzavni-organi/ministrstva/ministrstvo-za-kmetijstvo-gozdarstvo-in-prehrano/",
        "roles": ["producer", "licensor"]
    }
]

LICENSE = {
    "title": "Javno dostopni podatki: Publicly available data",
    "href": "https://rkg.gov.si/vstop/",
    "type": "text/html",
    "rel": "license"
}

COLUMNS = {
    "geometry": "geometry",
    "ID": "id",
    "GERK_PID": "block_id",
    "AREA": "area",
    "SIFRA_KMRS": "crop_code",
    "RASTLINA": "crop_name",
    "CROP_LAT_E": "crop_name_en",
}

COLUMN_MIGRATIONS = {
    "AREA": lambda col: col / 10000,
    "geometry": lambda col: col.make_valid()
}

MISSING_SCHEMAS = {
    "properties": {
        "block_id": {
            "type": "uint64"
        },
        "crop_name": {
            "type": "string"
        },
        "crop_code": {
            "type": "string"
        },
        "crop_name_en": {
            "type": "string"
        },
    }
}

COLUMNS, ADD_COLUMNS, EXTENSIONS = add_admin(vars(), "SI")


def convert(output_file, cache = None, mapping_file=None, **kwargs):
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
        missing_schemas=MISSING_SCHEMAS,
        column_additions=ADD_COLUMNS,
        column_migrations=COLUMN_MIGRATIONS,
        license=LICENSE,
        **kwargs
    )
