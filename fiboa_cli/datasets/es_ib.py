import re

import pandas as pd

from fiboa_cli.conversion.converter_rest import EsriRESTConverterMixin
from fiboa_cli.datasets.es import ESBaseConverter


class ESIBConverter(EsriRESTConverterMixin, ESBaseConverter):
    id = "es_ib"
    short_name = "Spain Balearic Islands"
    title = "Spain Balearic Islands Crop fields"
    description = """
    SIGPAC Crop fields of Spain - Balearic Islands
    """
    # https://www.caib.es/sites/M170613081930629/f/463418
    # see https://intranet.caib.es/opendatacataleg/dataset/sigpac-2024/resource/3a0bc2e0-3f37-45b7-a7d4-1e8c7cf09bc8
    license = "CC-BY-4.0"  # http://www.opendefinition.org/licenses/cc-by
    attribution = "Govern de les Illes Balears"
    providers = [
        {
            "name": "Govern de les Illes Balears",
            "url": "https://gobiernoabierto.navarra.es/",
            "roles": ["producer", "licensor"],
        }
    ]
    columns = {
        "DN_OID": "id",
        "geometry": "geometry",
        "PROVINCIA": "admin_province_code",
        "MUNICIPIO": "admin_municipality_code",
        "DN_SURFACE": "metrics:area",
        "USO_SIGPAC": "crop:code",
        "crop:name": "crop:name",
        "crop:name_en": "crop:name_en",
        "ANYS": "determination:datetime",
    }
    column_migrations = {
        "DN_SURFACE": lambda x: x / 10000,
        "ANYS": lambda col: pd.to_datetime(col, format="%Y"),
    }
    missing_schemas = {
        "properties": {
            "admin_province_code": {"type": "string"},
            "admin_municipality_code": {"type": "string"},
        }
    }

    # See https://ideib.caib.es/geoserveis/rest/services/public/GOIB_SIGPAC_IB/MapServer/ for current years
    variants = {str(year): str(year) for year in range(2024, 2010 - 1, -1)}
    use_code_attribute = "USO_SIGPAC"

    rest_base_url = "https://ideib.caib.es/geoserveis/rest/services/public/GOIB_SIGPAC_IB/MapServer"
    rest_params = {
        "where": "USO_SIGPAC NOT IN ('AG','CA','ED','FO','IM','IS','IV','TH','ZC','ZU','ZV','MT')"
    }

    def rest_layer_filter(self, layers):
        if not self.variant:
            self.variant = next(iter(self.variants))
        regex = re.compile("SIGPAC .* " + self.variant)
        return next(layer for layer in layers if regex.match(layer["name"]))
