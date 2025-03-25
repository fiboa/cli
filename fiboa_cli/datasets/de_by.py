from ..convert_utils import BaseConverter
from .commons.admin import AdminConverterMixin


class Converter(AdminConverterMixin, BaseConverter):
    sources = "https://geodaten.bayern.de/odd/m/3/daten/ln/landnutzung.gpkg"
    avoid_range_request = True

    id = "de_by"
    admin_subdivision_code = "BY"
    short_name = "Germany, Bavaria"
    title = "Field boundaries for Bavaria, Germany"
    description = """A field block (German: "Feldblock") is a contiguous agricultural area surrounded by permanent boundaries, which is cultivated by one or more farmers with one or more crops, is fully or partially set aside or is fully or partially taken out of production."""
    license = "CC-BY-4.0"
    attribution = "Datenquelle: Bayerische Vermessungsverwaltung – www.geodaten.bayern.de"
    providers = [
        {
            "name": "Bayerische Vermessungsverwaltung",
            "url": "https://www.ldbv.bayern.de",
            "roles": ["producer", "licensor"],
        }
    ]
    extensions = {"https://fiboa.github.io/flik-extension/v0.1.0/schema.yaml"}

    columns = {
        "geometry": "geometry",
        "objid": ["id", "flik"],
        "datumderletztenueberpruefung": "determination_datetime",
        "beginnt": "datetime:first_determination",
        "bewirtschaftung": "cultivation",
        # "artderbetriebsflaeche": "artderbetriebsflaeche",
        # "name": "name",
        # "istweiterenutzung": "istweiterenutzung",
        # "mappingannahme": "mappingannahme",
        "quellobjektid": "source_id",
    }
    missing_schemas = {
        "properties": {
            "datetime:first_determination": {"type": "date-time"},
            "cultivation": {"type": "string"},
            # "artderbetriebsflaeche": {"type": "string"},
            # "name": {"type": "string"},
            # "istweiterenutzung": {"type": "string"},
            # "mappingannahme": {"type": "boolean"},
            "source_id": {"type": "string"},
        }
    }

    column_filters = {
        # see https://www.adv-online.de/GeoInfoDok/Aktuelle-Anwendungsschemata/Landnutzung-1.0.2/binarywriterservlet?imgUid=be12989a-7b60-5819-393b-216067bef8a0&uBasVariant=11111111-1111-1111-1111-111111111111#_C10573-_A10573_44376
        "bewirtschaftung": lambda col: col.isin(
            ["1010", "1011", "1012", "1013", "1014", "1030", "1040", "1050"]
        )
    }

    def layer_filter(self, layer: str, uri: str) -> bool:
        return layer == "ln_landwirtschaft"
