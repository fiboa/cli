from ..convert_utils import BaseConverter

class PTConverter(BaseConverter):
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
            "roles": ["producer", "licensor"]
        }
    ]
    attribution = None
    license = {"title": "No conditions apply", "href": "https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply", "type": "text/html", "rel": "license"}
    columns = {
        "geometry": "geometry",
        "OSA_ID": "id",
        "CUL_ID": "block_id",
        "CUL_CODIGO": "crop_code",
        "CT_português": "crop_name",
        "Shape_Area": "area",
        "Shape_Length": "perimeter"
    }
    add_columns = {
        "determination_datetime": "2023-01-01T00:00:00Z"
    }
    column_migrations = {
        "Shape_Area": lambda col: col / 10000.0
    }
    missing_schemas = {
        "properties": {
            "block_id": {
                "type": "int64"
            },
            "crop_code": {
                "type": "string"
            },
            "crop_name": {
                "type": "string"
            },
        }
    }
