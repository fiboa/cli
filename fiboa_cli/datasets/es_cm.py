import re

import requests

from fiboa_cli.converter_rest import EsriRESTConverterMixin
from fiboa_cli.datasets.es import ESBaseConverter


class ESCMConverter(EsriRESTConverterMixin, ESBaseConverter):
    id = "es_cm"
    short_name = "Spain "
    title = "Spain Castilla-La Mancha Crop fields"
    description = """
    SIGPAC is a Geographic Information System dedicated to the control of agricultural aid under
    the CAP (Common Agricultural Policy). This tool is mandatory for the management of community aid, and is
    the identification basis for any type of aid related to the surface area."""
    license = "CC-BY-SA-4.0"  # see https://datosabiertos.castillalamancha.es/dataset/sistema-de-informaci%C3%B3n-geogr%C3%A1fica-de-parcelas-agr%C3%ADcolas-de-castilla-la-mancha-sigpac  # https://mapas.xunta.gal/gl/aviso-legal
    attribution = "Unidad de Cartografía. Secretaría General. Consejería de Agricultura , Ganadería y Desarrollo Rural."
    providers = [
        {
            "name": "Unidad de Cartografía. Secretaría General. Consejería de Agricultura , Ganadería y Desarrollo Rural.",
            "url": "https://datosabiertos.castillalamancha.es/",
            "roles": ["producer", "licensor"],
        }
    ]
    columns = {
        "dn_oid": "id",
        "geometry": "geometry",
        "provincia": "admin_province_code",
        "municipio": "admin_municipality_code",
        "dn_surface": "area",
        "uso_sigpac": "crop:code",
        "crop:name": "crop:name",
        "crop:name_en": "crop:name_en",
    }
    column_migrations = {
        "dn_surface": lambda x: x / 10000,
    }
    missing_schemas = {
        "properties": {
            "admin_province_code": {"type": "string"},
            "admin_municipality_code": {"type": "string"},
        }
    }
    source_variants = {str(year): str(year) for year in range(2024, 2018 - 1, -1)}

    rest_base_url = "https://geoservicios.castillalamancha.es/arcgis/rest/services/Vector"
    rest_attribute = "objectid_1"

    def get_urls(self):
        latest_variant = next(iter(self.source_variants))
        if not self.variant:
            self.variant = latest_variant
        if self.variant == latest_variant:
            layer = "Vector/Recintos_sigpac"
        else:
            services = requests.get(self.rest_base_url, {"f": "pjson"}).json()["services"]
            layer = next(
                s["name"]
                for s in services
                if re.search(f"Recintos_sigpac_{self.variant}", s["name"], re.IGNORECASE)
            )
        return {"REST": self.rest_base_url.replace("Vector", layer + "/MapServer")}
