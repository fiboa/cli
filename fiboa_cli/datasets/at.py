from ..convert_utils import BaseConverter
from .commons.admin import AdminConverterMixin


class Converter(AdminConverterMixin, BaseConverter):
    sources = {
        "https://inspire.lfrz.gv.at/009501/ds/inspire_referenzen_2021_polygon.gpkg.zip": [
            "INSPIRE_REFERENZEN_2021_POLYGON.gpkg"
        ]
    }
    id = "at"
    country = "AT"
    short_name = "Austria"
    title = "Field boundaries for Austria"
    description = """
    **Field boundaries for Austria - INVEKOS Referenzen Österreich 2021.**

    The layer includes all reference parcels ("Referenzparzellen") defined by the paying agency Agrarmarkt Austria and recorded landscape elements (landscape element layers) within the meaning of Art. 5 of Regulation (EU) No. 640/2014 and Regulation of the competent federal ministry with horizontal rules for the area of the Common Agricultural Policy (Horizontal CAP Regulation) StF: Federal Law Gazette II No. 100/2015.

    Reference parcel: is the physical block that can be clearly delimited from the outside (e.g. forest, roads, water bodies) and is formed by contiguous agricultural areas that are recognizable in nature.
    """
    providers = [
        {
            "name": "Agrarmarkt Austria",
            "url": "https://geometadatensuche.inspire.gv.at/metadatensuche/inspire/api/records/9db8a0c3-e92a-4df4-9d55-8210e326a7ed",
            "roles": ["producer", "licensor"],
        }
    ]
    license = "CC-BY-4.0"
    columns = {
        "geometry": "geometry",
        "RFL_ID": "id",
        "REF_ART": "ref_art",
        "BRUTTOFLAECHE_HA": "area",
        "INSPIRE_ID": "inspire:id",
        "REF_ART_BEZEICHNUNG": "ref_art_bezeichnung",
        "REFERENZ_KENNUNG": "referenz_kennung",
        "FART_ID": "fart_id",
        "GEO_DATERF": "determination_datetime",
    }
    extensions = {"https://fiboa.github.io/inspire-extension/v0.2.0/schema.yaml"}
    missing_schemas = {
        "properties": {
            "ref_art": {"type": "string"},
            "ref_art_bezeichnung": {"type": "string"},
            "referenz_kennung": {"type": "uint64"},
            "fart_id": {"type": "uint32"},
        }
    }
