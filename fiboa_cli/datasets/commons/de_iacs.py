from .code_list import CodeListMixin

# Nationally governed codelist of the German IACS/InVeKoS data, maintained by the
# Bundesministerium für Ernährung und Landwirtschaft in the GDI-DE registry:
# https://registry.gdi-de.org/codelist/de.iacs/AgriculturalAreaTypeValue
# Values: AL (Ackerland), GL (Dauergrünland), DK (Dauerkultur), AF (Agroforst), S (Sonstiges)
CODE_LIST = "https://fiboa.org/code/de/iacs/agricultural_area_type.csv"
CODE_LIST_FILE = "de_iacs_area_types.csv"


class DEIACSMixin(CodeListMixin):
    """
    Maps the German IACS land cover class ("Bodenbedeckung" / agriculturalAreaType) onto the
    crop extension, so that the federal states share one column and one vocabulary.

    Converters map their source attribute to crop:code; the German and English names are derived
    here from the shared code list, so every state emits identical strings for the same code.
    """

    code_list = CODE_LIST
    code_list_file = CODE_LIST_FILE
