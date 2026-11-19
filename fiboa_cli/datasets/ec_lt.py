from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import EuroCropsConverterMixin


class Converter(EuroCropsConverterMixin, FiboaBaseConverter):
    area_is_in_ha = False
    hcat_mapping_csv = "https://fiboa.org/code/lt/lt_2021.csv"
    ec_year = 2021
    hcat_columns = {
        "hcat:name_en": "hcat:name_en",
        "hcat:name": "hcat:name",
        "hcat:code": "hcat:code",
    }
    sources = {"https://zenodo.org/records/6868143/files/LT_2021.zip": ["LT/LT_2021_EC.shp"]}
    # the DBF is CP1257 and carries no .cpg
    open_options = dict(encoding="cp1257")

    id = "ec_lt"
    short_name = "Lithuania"
    title = "Field boundaries for Lithuania"
    description = """
Collection of data on agricultural land and crop areas, cultivated crops in the territory of the Republic of Lithuania.

The download service is a set of personalized spatial data of agricultural land and crop areas, cultivated crops. The service provides object geometry with descriptive (attributive) data.
    """
    provider = "Construction Sector Development Agency <https://www.geoportal.lt/geoportal/nacionaline-mokejimo-agentura-prie-zemes-ukio-ministerijos#savedSearchId={56542726-DC0B-461E-A32C-3E9A4A693E27}&collapsed=true>"
    # license = "Non-commercial use only <https://www.geoportal.lt/metadata-catalog/catalog/search/resource/details.page?uuid=%7B7AF3F5B2-DC58-4EC5-916C-813E994B2DCF%7D>"

    columns = {
        "NMA_ID": "claimant_id",
        "GRUPE": ["crop:name", "crop:code"],  # the code list is keyed on the name
        "Shape_Leng": "metrics:perimeter",
        "Shape_Area": "metrics:area",
        "geometry": "geometry",
    }
    column_additions = {"determination:datetime": "2021-10-08T00:00:00Z"}
    # The groups that are crops; the rest is grassland, forest, ditches,
    # wetlands, fallow and other land cover.
    CROP_GROUPS = [
        "Daržovės",
        "Grikiai",
        "Ankštiniai javai",
        "Avižos",
        "Žieminiai javai",
        "Vasariniai javai",
        "Cukriniai runkeliai",
        "Uogynai",
        "Kukurūzai",
    ]
    column_filters = {"GRUPE": lambda col: (col.isin(Converter.CROP_GROUPS), False)}

    missing_schemas = {"properties": {"claimant_id": {"type": "int64"}}}
