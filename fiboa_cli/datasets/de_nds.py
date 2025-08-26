from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter


class Converter(AdminConverterMixin, FiboaBaseConverter):
    sources = "https://sla.niedersachsen.de/mapbender_sla/download/FB_NDS.zip"
    id = "de_nds"
    admin_subdivision_code = "NI"
    short_name = "Germany, Lower Saxony/Bremen/Hamburg"
    title = "Field boundaries for Lower Saxony / Bremen / Hamburg, Germany"
    description = """A field block (German: "Feldblock") is a contiguous agricultural area surrounded by permanent boundaries, which is cultivated by one or more farmers with one or more crops, is fully or partially set aside or is fully or partially taken out of production."""
    providers = [
        {
            "name": "ML/SLA Niedersachsen",
            "url": "https://sla.niedersachsen.de/landentwicklung/LEA/",
            "roles": ["producer", "licensor"],
        }
    ]
    attribution = "© ML/SLA Niedersachsen (2024), dl-de/by-2-0 (www.govdata.de/dl-de/by-2-0), Daten bearbeitet"
    license = "dl-de/by-2-0"
    extensions = {"https://fiboa.github.io/flik-extension/v0.2.0/schema.yaml"}
    columns = {
        "geometry": "geometry",
        "FLIK": ["id", "flik"],
        "STAND": "determination:datetime",
        "ANT_JAHR": "ant_jahr",
        "BNK": "bnk",
        "BNK_TXT": "bnk_txt",
        "FLAECHE": "metrics:area",
        "SHAPE_Leng": "metrics:perimeter",
    }
    missing_schemas = {
        "properties": {
            "ant_jahr": {"type": "int16"},
            "bnk": {"type": "string"},
            "bnk_txt": {"type": "string"},
        }
    }
