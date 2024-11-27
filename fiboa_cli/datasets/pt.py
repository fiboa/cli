from ..convert_utils import convert as convert_
from .commons.admin import add_admin

SOURCES = "https://www.ifap.pt/isip/ows/resources/2023/Continente.gpkg"
#SOURCES = "https://www.ifap.pt/isip/ows/resources/2022/2022.zip"
LAYER_FILTER = lambda layer, uri: layer.startswith("Culturas_")

ID = "pt"
TITLE = "Field boundaries for Portugal"
SHORT_NAME = "Portugal"
DESCRIPTION = "Open field boundaries (identificação de parcelas) from Portugal"
PROVIDERS = [
    {
        "name": "IPAP - Instituto de Financiamento da Agricultura e Pescas",
        "url": "https://www.ifap.pt/isip/ows/",
        "roles": ["producer", "licensor"]
    }
]
ATTRIBUTION = None

# Inspire license. Not 100% clear at source
LICENSE = {"title": "No conditions apply", "href": "https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply", "type": "text/html", "rel": "license"}

COLUMNS = {
    "geometry": "geometry",
    "OSA_ID": "id",
    "CUL_ID": "block_id",
    "CUL_CODIGO": "crop_code",
    "CT_português": "crop_name",
    "Shape_Area": "area",
    "Shape_Length": "perimeter"
}

ADD_COLUMNS = {
    "determination_datetime": "2023-01-01T00:00:00Z"
}

COLUMN_MIGRATIONS = {
    "Shape_Area": lambda col: col / 10000.0
}

MISSING_SCHEMAS = {
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

COLUMNS, ADD_COLUMNS, EXTENSIONS = add_admin(vars(), "PT")


def convert(output_file, cache = None, **kwargs):
    convert_(
        output_file,
        cache,
        SOURCES,
        COLUMNS,
        ID,
        TITLE,
        DESCRIPTION,
        providers=PROVIDERS,
        extensions=EXTENSIONS,
        missing_schemas=MISSING_SCHEMAS,
        column_additions=ADD_COLUMNS,
        column_migrations=COLUMN_MIGRATIONS,
        attribution=ATTRIBUTION,
        license=LICENSE,
        layer_filter=LAYER_FILTER,
        **kwargs
    )
