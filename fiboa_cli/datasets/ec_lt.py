from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import EuroCropsConverterMixin


class Converter(EuroCropsConverterMixin, FiboaBaseConverter):
    area_is_in_ha = False
    # EuroCrops' own table carries the same mangled names. This copy spells them
    # correctly and fixes the two mappings guessed from the mangled text
    # (Šlapynės is wetlands, not spinach; Ankštiniai javai is leguminous).
    ec_mapping_csv = "https://fiboa.org/code/lt/lt_2021.csv"
    ec_year = 2021
    # The file's own EC_hcat_* columns hold the mapping derived from the mangled
    # names, so they are ignored and the table above is used instead.
    hcat_columns = {
        "hcat:name_en": "hcat:name_en",
        "hcat:name": "hcat:name",
        "hcat:code": "hcat:code",
    }
    sources = {"https://zenodo.org/records/6868143/files/LT_2021.zip": ["LT/LT_2021_EC.shp"]}

    id = "ec_lt"
    short_name = "Lithuania"
    title = "Field boundaries for Lithuania"
    description = """
Collection of data on agricultural land and crop areas, cultivated crops in the territory of the Republic of Lithuania.

The download service is a set of personalized spatial data of agricultural land and crop areas, cultivated crops. The service provides object geometry with descriptive (attributive) data.
    """
    provider = "Construction Sector Development Agency <https://www.geoportal.lt/geoportal/nacionaline-mokejimo-agentura-prie-zemes-ukio-ministerijos#savedSearchId={56542726-DC0B-461E-A32C-3E9A4A693E27}&collapsed=true>"
    # license = "Non-commercial use only <https://www.geoportal.lt/metadata-catalog/catalog/search/resource/details.page?uuid=%7B7AF3F5B2-DC58-4EC5-916C-813E994B2DCF%7D>"

    # Nothing identifies a parcel: KZS_NR is the land-register block, NMA_ID the
    # claimant, and adding GRUPE and the area still leaves 3,991 of 1,102,471
    # rows sharing a key. Safe here because the release is one file.
    index_as_id = True
    columns = {
        "id": "id",
        "NMA_ID": "claimant_id",
        "GRUPE": "crop:name",
        "Shape_Leng": "metrics:perimeter",
        "Shape_Area": "metrics:area",
        "geometry": "geometry",
    }
    add_columns = {"determination:datetime": "2021-10-08T00:00:00Z"}
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

    def migrate(self, gdf):
        # The release ships Lithuanian run through the wrong code page and saved
        # as UTF-8: it decodes cleanly to "Ankðtiniai javai". Latin-1 out,
        # CP1257 in undoes that and leaves a correct name untouched.
        if "GRUPE" in gdf.columns:
            gdf["GRUPE"] = gdf["GRUPE"].map(self._repair_baltic_text)
        return super().migrate(gdf)

    @staticmethod
    def _repair_baltic_text(value):
        if not isinstance(value, str):
            return value
        try:
            return value.encode("latin-1").decode("cp1257")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return value

    # Two of these used to be declared, and the second silently replaced the
    # first, so claimant_id reached the writer with no schema at all.
    missing_schemas = {"required": [], "properties": {"claimant_id": {"type": "int64"}}}
