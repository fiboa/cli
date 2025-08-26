from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import ec_url


class PTConverter(FiboaBaseConverter):
    id = "pt"
    title = "Field boundaries for Portugal"
    short_name = "Portugal"
    description = "Open field boundaries (identificação de parcelas) from Portugal"
    sources = "https://www.ifap.pt/isip/ows/resources/2023/Continente.gpkg"

    def layer_filter(self, layer, uri):
        return layer.startswith("Culturas_")

    providers = [
        {
            "name": "IPAP - Instituto de Financiamento da Agricultura e Pescas",
            "url": "https://www.ifap.pt/isip/ows/",
            "roles": ["producer", "licensor"],
        }
    ]
    license = {
        "title": "No conditions apply",
        "href": "https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply",
        "type": "text/html",
        "rel": "license",
    }
    columns = {
        "geometry": "geometry",
        "OSA_ID": "id",
        "CUL_ID": "block_id",
        "CUL_CODIGO": "crop:code",
        "CT_português": "crop:name",
        "Shape_Area": "metrics:area",
        "Shape_Length": "metrics:perimeter",
    }
    extensions = {"https://fiboa.github.io/crop-extension/v0.2.0/schema.yaml"}
    column_additions = {
        "crop:code_list": ec_url("pt_2021.csv"),
        "determination:datetime": "2023-01-01T00:00:00Z",
    }
    column_migrations = {"Shape_Area": lambda col: col / 10000.0}
    missing_schemas = {
        "properties": {
            "block_id": {"type": "int64"},
        }
    }
