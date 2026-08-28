from .data import read_data_csv
from .hcat import CROP_EXTENSION

# Nationally governed codelist of the German IACS/InVeKoS data, maintained by the
# Bundesministerium für Ernährung und Landwirtschaft in the GDI-DE registry:
# https://registry.gdi-de.org/codelist/de.iacs/AgriculturalAreaTypeValue
# Values: AL (Ackerland), GL (Dauergrünland), DK (Dauerkultur), AF (Agroforst), S (Sonstiges)
CODE_LIST = "https://fiboa.org/code/de/iacs/agricultural_area_type.csv"
CODE_LIST_FILE = "de_iacs_area_types.csv"


class DEIACSMixin:
    """
    Maps the German IACS land cover class ("Bodenbedeckung" / agriculturalAreaType) onto the
    crop extension, so that the federal states share one column and one vocabulary.

    Converters map their source attribute to crop:code; the German and English names are derived
    here from the shared code list, so every state emits identical strings for the same code.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rebind instead of mutating: the class-level dicts are shared with AdminConverterMixin,
        # and a converter's own `extensions` would otherwise replace the crop extension.
        self.extensions = set(self.extensions) | {CROP_EXTENSION}
        self.columns = {
            **self.columns,
            "crop:name": "crop:name",
            "crop:name_en": "crop:name_en",
            "crop:code_list": "crop:code_list",
        }

    def post_migrate(self, gdf):
        gdf = super().post_migrate(gdf)
        # Look up the source attribute that the converter mapped to crop:code, the same way
        # AddHCATMixin.get_code_column does. Columns are still source-named at this point.
        attribute = next(k for k, v in self.columns.items() if v == "crop:code")
        rows = read_data_csv(CODE_LIST_FILE)
        codes = gdf[attribute]
        gdf["crop:name"] = codes.map({r["original_code"]: r["original_name"] for r in rows})
        gdf["crop:name_en"] = codes.map({r["original_code"]: r["name_en"] for r in rows})
        gdf["crop:code_list"] = CODE_LIST
        return gdf
