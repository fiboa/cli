from ..convert_utils import convert as convert_
from .commons.ec import add_eurocrops

SOURCES = {"https://zenodo.org/records/6868143/files/LT_2021.zip": ["LT/LT_2021_EC.shp"]}

ID = "ec_lt"
SHORT_NAME = "Lithuania"
TITLE = "Field boundaries for Lithuania"
DESCRIPTION = """
Collection of data on agricultural land and crop areas, cultivated crops in the territory of the Republic of Lithuania.

The download service is a set of personalized spatial data of agricultural land and crop areas, cultivated crops. The service provides object geometry with descriptive (attributive) data.
"""
PROVIDERS = [
    {
        "name": "Construction Sector Development Agency",
        "url": "https://www.geoportal.lt/geoportal/nacionaline-mokejimo-agentura-prie-zemes-ukio-ministerijos#savedSearchId={56542726-DC0B-461E-A32C-3E9A4A693E27}&collapsed=true",
        "roles": ["producer", "licensor"],
    }
]
# LICENSE = {"title": "Non-commercial use only", "href": "https://www.geoportal.lt/metadata-catalog/catalog/search/resource/details.page?uuid=%7B7AF3F5B2-DC58-4EC5-916C-813E994B2DCF%7D", "type": "text/html", "rel": "license"}

COLUMNS = {
    "NMA_ID": "id",
    "GRUPE": "crop_name",
    "Shape_Leng": "perimeter",
    "Shape_Area": "area",
    "geometry": "geometry",
}
ADD_COLUMNS = {"determination_datetime": "2021-10-08T00:00:00Z"}
COLUMN_MIGRATIONS = {"Shape_Area": lambda column: column * 0.0001}
COLUMN_FILTERS = {
    "GRUPE": lambda col: (
        col.isin(
            [
                "Darþovës",
                "Grikiai",
                "Ankðtiniai javai",
                "Aviþos",
                "Þieminiai javai",
                "Summer Cereals",
                "Vasariniai javai",
                "Cukriniai runkeliai",
                "Uogynai",
                "Kukurûzai",
            ]
        ),
        False,
    )
}

MISSING_SCHEMAS = {"required": [], "properties": {"crop_name": {"type": "string"}}}

ID, SHORT_NAME, TITLE, DESCRIPTION, PROVIDERS, EXTENSIONS, COLUMNS, LICENSE = add_eurocrops(
    vars(), 2021
)


# Conversion function, usually no changes required
def convert(output_file, cache=None, **kwargs):
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
        column_filters=COLUMN_FILTERS,
        license=LICENSE,
        **kwargs,
    )
