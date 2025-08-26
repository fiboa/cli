from fiboa_cli.conversion.converter_rest import EsriRESTConverterMixin
from fiboa_cli.datasets.es import ESBaseConverter


class ESGAConverter(EsriRESTConverterMixin, ESBaseConverter):
    id = "es_ga"
    short_name = "Spain "
    title = "Spain Galicia Crop fields"
    description = """
    Galician Crop Fields
    The Geographic Information System for Agricultural Plots (SIXPAC) is an official reference database for the identification of agricultural plots, which is mandatory in Spain for making applications for direct CAP aid that require declaring surface areas.
    SIXPAC information is relevant to farmers applying for these aid schemes, so that they can indicate the location of the farm surfaces that may be eligible for subsidies, as well as to facilitate the submission of requests for changes to data relating to land uses contained in the system.
    """
    license = "CC-BY-4.0"  # https://mapas.xunta.gal/gl/aviso-legal
    attribution = "Información procedente do FOGGA"
    providers = [
        {
            "name": "Virtual Office for Rural Environment",
            "url": "https://ovmediorural.xunta.gal/es/consultas-publicas/sixpac",
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

    rest_base_url = (
        "https://ideg.xunta.gal/servizos/rest/services/ParcelasCatastrais/SIXPAC_{year}/MapServer"
    )

    def rest_layer_filter(self, layers):
        return next(layer for layer in layers if "recintos" in layer["name"].lower())

    def get_urls(self):
        if not self.variant:
            self.variant = next(iter(self.variants))
        return {"REST": self.rest_base_url.format(year=self.variant)}
