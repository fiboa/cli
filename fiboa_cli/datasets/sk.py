from ..convert_utils import convert as convert_
from .commons.admin import add_admin

SOURCES = {
    "https://data.slovensko.sk/download?id=e39ad227-1899-4cff-b7c8-734f90aa0b59&blocksize=0": [
        "HU2024_20240917shp/HU2024_20240917.shp"
    ]
}
ID = "sk"
SHORT_NAME = "Slovakia"
TITLE = "Slowakia Agricultural Land Idenfitication System"

DESCRIPTION = """
Systém identifikácie poľnohospodárskych pozemkov (LPIS)

LPIS is an agricultural land identification system. It represents the vector boundaries of agricultural land
and carries information about the unique code, acreage, culture/land use, etc., which is used as a reference
for farmers' applications, for administrative and cross-checks, on-site checks and also checks using remote
sensing methods.

Dataset Hranice užívania contains the use declared by applicants for direct support.
"""
PROVIDERS = [
    {
        "name": "National catalog of open data",
        "url": "https://data.slovensko.sk/",
        "roles": ["producer", "licensor"]
    }
]

LICENSE = "CC-0"  # "Open Data"
COLUMNS = {
    "geometry": "geometry",
    "KODKD": "id",
    "PLODINA": "crop_name",
    "KULTURA_NA": "crop_group",
    "LOKALITA_N": "municipality",
    "VYMERA": "area",
}
COLUMN_MIGRATIONS = {
    "geometry": lambda col: col.make_valid()
}
MISSING_SCHEMAS = {
    "properties": {
        "crop_name": {
            "type": "string"
        },
        "crop_group": {
            "type": "string"
        },
        "municipality": {
            "type": "string"
        },
    }
}

COLUMNS, ADD_COLUMNS, EXTENSIONS = add_admin(vars(), "SK")


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
        missing_schemas=MISSING_SCHEMAS,
        column_additions=ADD_COLUMNS,
        license=LICENSE,
        column_migrations=COLUMN_MIGRATIONS,
        **kwargs
    )
