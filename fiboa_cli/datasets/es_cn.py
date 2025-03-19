import pandas as pd

from fiboa_cli.convert_utils import BaseConverter


class ESCNConverter(BaseConverter):
    id = "es_cn"
    short_name = "Spain Canary Islands"
    title = "Spain Crop fields of Canary Islands"
    description = """
    The Canary Islands Crop Map is a cartographic dataset developed by the Department of Agriculture, Livestock,
    Fisheries and Water of the Government of the Canary Islands, to understand the reality of the available
    agricultural surface of the Canary Islands. This tool has been developed from 1998 to the present.

    There are several crop maps for each of the islands, which allow us to see the temporal and spatial evolution
    of the cultivated areas of the islands in recent years. All this means that the Canary Islands Crop Map is a
    basic tool for decision-making in present and future regional agricultural policy, as well as being a basic
    source for the preservation of agricultural land in the field of territorial planning.

    The data of the Canary Islands Crop Map have been published on the open data portal of
    the Government of the Canary Islands (https://datos.canarias.es/catalogos/general/dataset/mapa-de-cultivos-de-canarias)
    and in datos gob (https://datos.gob.es/es/catalogo/a05003638-mapa-de-cultivos-de-canarias1),
    this work having been addressed within the Strategic Plan for Innovation and Continuous Improvement
    of the Ministry of Agriculture, Livestock and Fisheries.
    """
    providers = [
        {
            "name": "Gobierno de Canarias - Consejería de Agricultura, Ganadería, Pesca y Soberanía Alimentaria",
            "url": "https://www.gobiernodecanarias.org/agpsa/",
            "roles": ["producer", "licensor"],
        }
    ]
    license = "CC-BY-4.0"  # as stated in https://datos.canarias.es/portal/aviso-legal-y-condiciones-de-uso
    attribution = "Gobierno de Canarias"
    extensions = {
        "https://fiboa.github.io/crop-extension/v0.1.0/schema.yaml",
        "https://fiboa.github.io/administrative-division-extension/v0.1.0/schema.yaml",
    }
    columns = {
        "id": "id",
        "geometry": "geometry",
        "FECHA": "determination_datetime",
        "ISLA_NA": "admin_island",
        "CULTIVO_CO": "crop:code",
        "CULTIVO_NA": "crop:name",
        "AREA_M2": "area",
    }
    column_migrations = {
        "AREA_M2": lambda column: column / 10000,
        "FECHA": lambda column: pd.to_datetime(column, format="%d/%m/%Y"),
    }
    column_additions = {
        "admin:country_code": "ES",
        "admin:subdivision_code": "CB",
        "crop:code_list": "https://fiboa.org/code/es/cn/crop.csv",
    }
    missing_schemas = {
        "properties": {
            "admin_island": {"type": "string"},
        }
    }
    index_as_id = True
    sources = {
        f"https://opendata.sitcan.es/upload/medio-rural/gobcan_mapa-cultivos_{island}_shp.zip": f"gobcan_mapa-cultivos_{island}_shp.zip"
        for island in "lz eh lp lg tf gc fv".split()
    }
    # Create code list with:
    # duckdb -c 'SELECT distinct "crop:code", "crop:name" FROM "es_cn.parquet" order by "crop:code"'
