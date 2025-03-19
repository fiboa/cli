import pandas as pd

from ..convert_utils import BaseConverter
from .commons.admin import AdminConverterMixin


class Converter(AdminConverterMixin, BaseConverter):
    sources = {
        "https://www.smul.sachsen.de/gis-online/download/FBZ_ISS_Bereiche/gesamt_2024_RE.zip": [
            "2024_RE_FB_33.shp"
        ]
    }
    id = "de_sax"
    admin_subdivision_code = "SN"
    short_name = "Germany, Saxony"
    title = "Field boundaries for Saxony, Germany"
    description = "Feldblöcke und förderfähige Elemente in Sachsen 2024"
    providers = [
        {
            "name": "Sächsisches Landesamt für Umwelt, Landwirtschaft und Geologie",
            "url": "https://geoportal.sachsen.de/",
            "roles": ["producer", "licensor"],
        }
    ]
    attribution = "Sächsisches Landesamt für Umwelt, Landwirtschaft und Geologie"
    license = "dl-de/by-2-0"
    extensions = {"https://fiboa.github.io/flik-extension/v0.1.0/schema.yaml"}
    columns = {
        "geometry": "geometry",
        "FB_FLIK": ["id", "flik"],
        "JAHR": "determination_datetime",
        "FB_A_FLAE": "area",
        "FB_BN_KAT": "FB_BN_KAT",
        "FB_BEZEICH": "FB_BEZEICH",
        "ZUSTAENDIG": "ZUSTAENDIG",
        "FB_FFH": "FB_FFH",
        "FB_SPA": "FB_SPA",
        "FB_NB": "FB_NB",
        "NITRAT": "NITRAT",
        "WT_WRRL": "WT_WRRL",
        "NITRAT_TG": "NITRAT_TG",
        "KWIND": "KWIND",
        "KWASSER": "KWASSER",
        "AGROFORST": "AGROFORST",
        "AGRIPV": "AGRIPV",
        "GLOEZ2": "GLOEZ2",
        "OER_UNZUL": "OER_UNZUL",
        "REG_SAAT": "REG_SAAT",
        "BERG": "BERG",
    }
    missing_schemas = {
        "properties": {
            "FB_BN_KAT": {"type": "string"},
            "FB_BEZEICH": {"type": "string"},
            "ZUSTAENDIG": {"type": "uint8"},
            "FB_FFH": {"type": "boolean"},
            "FB_SPA": {"type": "boolean"},
            "FB_NB": {"type": "string"},
            "NITRAT": {"type": "boolean"},
            "WT_WRRL": {"type": "boolean"},
            "NITRAT_TG": {"type": "boolean"},
            "KWIND": {"type": "uint8"},
            "KWASSER": {"type": "uint8"},
            "AGROFORST": {"type": "boolean"},
            "AGRIPV": {"type": "boolean"},
            "GLOEZ2": {"type": "boolean"},
            "OER_UNZUL": {"type": "string"},
            "REG_SAAT": {"type": "string"},
            "BERG": {"type": "uint8"},
        }
    }
    column_migrations = {"JAHR": lambda col: pd.to_datetime(col, format="%Y")}
    # Add boolean column migrations dynamically
    for key, schema in missing_schemas["properties"].items():
        if schema["type"] == "boolean":
            column_migrations[key] = lambda col: col.map({"J": True, "N": False}).astype(bool)
