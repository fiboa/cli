import re

from fiboa_cli.conversion.converter_rest import EsriRESTConverterMixin
from fiboa_cli.datasets.es import ESBaseConverter


class ESCBConverter(EsriRESTConverterMixin, ESBaseConverter):
    id = "es_cb"
    short_name = "Spain Cantabria"
    title = "Spain Cantabria Crop fields"
    description = """
    SIGPAC Crop fields of Spain - Cantabria
    """
    # https://www.caib.es/sites/M170613081930629/f/463418
    # see https://intranet.caib.es/opendatacataleg/dataset/sigpac-2024/resource/3a0bc2e0-3f37-45b7-a7d4-1e8c7cf09bc8
    # "Our licenses allow the reproduction or redistribution of the licensed digital information to third parties. In such cases, it is essential that when redistributing or transferring the data to said third parties, they clearly and explicitly accept the conditions of our non-commercial use license."
    license = "CC-BY-NC-4.0"  # http://www.opendefinition.org/licenses/cc-by
    attribution = (
        "©Government of Cantabria. Free information available at https://mapas.cantabria.es"
    )
    providers = [{"name": "", "url": "", "roles": ["producer", "licensor"]}]
    columns = {
        "DN_OID": "id",
        "geometry": "geometry",
        "PROVINCIA": "admin_province_code",
        "MUNICIPIO": "admin_municipality_code",
        "DN_SURFACE": "metrics:area",
        "USO_SIGPAC": "crop:code",
        "crop:name": "crop:name",
        "crop:name_en": "crop:name_en",
    }
    column_migrations = {
        "DN_SURFACE": lambda x: x / 10000,
    }
    missing_schemas = {
        "properties": {
            "admin_province_code": {"type": "string"},
            "admin_municipality_code": {"type": "string"},
        }
    }

    variants = {str(year): str(year) for year in range(2024, 2010 - 1, -1)}
    use_code_attribute = "USO_SIGPAC"

    # "https://geoservicios.cantabria.es/inspire/rest/services/SIGPAC/MapServer?f=json"
    # "https://geoservicios.cantabria.es/inspire/rest/services/SIGPAC/MapServer/63/query?f=json&where=1%3D1&spatialRel=esriSpatialRelIntersects&geometry=%7B%22xmin%22%3A407913.2828037373%2C%22ymin%22%3A4804384.359524686%2C%22xmax%22%3A411054.4224193499%2C%22ymax%22%3A4805366.49482229%2C%22spatialReference%22%3A%7B%22wkid%22%3A25830%2C%22latestWkid%22%3A25830%7D%7D&geometryType=esriGeometryEnvelope&inSR=25830&outFields=OBJECTID%2CPROVINCIA%2CMUNICIPIO%2CAGREGADO%2CZONA%2CPOLIGONO%2CPARCELA%2CRECINTO%2CUSO_SIGPAC%2CSHAPE_Area&orderByFields=OBJECTID%20ASC&outSR=25830"

    rest_base_url = "https://geoservicios.cantabria.es/inspire/rest/services/SIGPAC/MapServer"
    # rest_params = {"where": "USO_SIGPAC NOT IN ('AG','CA','ED','FO','IM','IS','IV','TH','ZC','ZU','ZV','MT')"}

    def rest_layer_filter(self, layers):
        if not self.variant:
            self.variant = next(iter(self.variants))
        self.column_additions["determination:datetime"] = ""
        regex = re.compile("Recintos SIGPAC " + self.variant)
        return next(layer for layer in layers if regex.match(layer["name"]))
