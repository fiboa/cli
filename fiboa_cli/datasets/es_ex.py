from .commons.sigpac import SigpacRecintoMixin
from .es_base import ESBaseConverter


class EXConverter(SigpacRecintoMixin, ESBaseConverter):
    id = "es_ex"
    # Badajoz and Cáceres
    provinces = ("06", "10")
    short_name = "Spain Extremadura"
    title = "Spain Extremadura Crop fields"
    description = """SIGPAC recintos of Extremadura, from the national release by the Spanish
paying agency. The region's own download portal (sitex.gobex.es) has not answered since at
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
    }
    missing_schemas = {
        "properties": {
            "admin_province_code": {"type": "string"},
            "admin_municipality_code": {"type": "string"},
        }
    }
