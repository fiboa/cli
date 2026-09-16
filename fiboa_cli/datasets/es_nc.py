from .commons.sigpac import SigpacRecintoMixin
from .es_base import ESBaseConverter


class NCConverter(SigpacRecintoMixin, ESBaseConverter):
    id = "es_nc"
    # Navarra is one province
    provinces = ("31",)
    short_name = "Spain Navarra"
    title = "Spain Navarra Crop fields"
    description = """SIGPAC recintos of Navarra, from the national release by the Spanish
paying agency. The region’s own download portal (sigpac.navarra.es) has not answered since at
least 2026-09-10."""
    license = "CC-BY-4.0"
    attribution = "©FEGA / Ministerio de Agricultura, Pesca y Alimentación"
    provider = "Fondo Español de Garantía Agraria (FEGA) <https://www.fega.gob.es>"

    columns = {
        "geometry": "geometry",
        "id": "id",
        "provincia": "admin_province_code",
        "municipio": "admin_municipality_code",
        "uso_sigpac": "crop:code",
        "crop:name": "crop:name",
        "crop:name_en": "crop:name_en",
        "dn_surface": "metrics:area",
        "determination:datetime": "determination:datetime",  # the campaign, from the variant
    }
    missing_schemas = {
        "properties": {
            "admin_province_code": {"type": "string"},
            "admin_municipality_code": {"type": "string"},
        }
    }
