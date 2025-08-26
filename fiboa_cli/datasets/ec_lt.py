from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import EuroCropsConverterMixin


class Converter(EuroCropsConverterMixin, FiboaBaseConverter):
    ec_mapping_csv = "lt_2021.csv"
    ec_year = 2021
    sources = {"https://zenodo.org/records/6868143/files/LT_2021.zip": ["LT/LT_2021_EC.shp"]}

    id = "ec_lt"
    short_name = "Lithuania"
    title = "Field boundaries for Lithuania"
    description = """
    Collection of data on agricultural land and crop areas, cultivated crops in the territory of the Republic of Lithuania.

    The download service is a set of personalized spatial data of agricultural land and crop areas, cultivated crops. The service provides object geometry with descriptive (attributive) data.
    """
    providers = [
        {
            "name": "Construction Sector Development Agency",
            "url": "https://www.geoportal.lt/geoportal/nacionaline-mokejimo-agentura-prie-zemes-ukio-ministerijos#savedSearchId={56542726-DC0B-461E-A32C-3E9A4A693E27}&collapsed=true",
            "roles": ["producer", "licensor"],
        }
    ]
    # license = {"title": "Non-commercial use only", "href": "https://www.geoportal.lt/metadata-catalog/catalog/search/resource/details.page?uuid=%7B7AF3F5B2-DC58-4EC5-916C-813E994B2DCF%7D", "type": "text/html", "rel": "license"}

    columns = {
        "NMA_ID": "id",
        "GRUPE": "crop:name",
        "Shape_Leng": "metrics:perimeter",
        "Shape_Area": "metrics:area",
        "geometry": "geometry",
    }
    add_columns = {"determination:datetime": "2021-10-08T00:00:00Z"}
    column_migrations = {"Shape_Area": lambda column: column * 0.0001}
    column_filters = {
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

    missing_schemas = {"required": [], "properties": {"crop_name": {"type": "string"}}}
