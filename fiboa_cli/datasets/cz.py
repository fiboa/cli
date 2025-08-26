import pandas as pd
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import ec_url


class Converter(AdminConverterMixin, FiboaBaseConverter):
    sources = "https://mze.gov.cz/public/app/eagriapp/Files/geoprostor_zadosti23_2024-08-01_202409261243_epsg4258.zip"
    id = "cz"
    short_name = "Czech"
    title = "Field boundaries for Czech"
    description = "The cropfields of Czech (Plodina)"
    providers = [
        {
            "name": "Czech Ministry of Agriculture (Ministr Zemědělství)",
            "url": "https://mze.gov.cz/public/portal/mze/farmar/LPIS",
            "roles": ["producer", "licensor"],
        }
    ]
    license = "CC-0"
    columns = {
        "geometry": "geometry",
        "ZAKRES_ID": "id",
        "DPB_ID": "block_id",
        "PLODINA_ID": "crop:code",
        "PLOD_NAZE": "crop:name",
        "ZAKRES_VYM": "metrics:area",
        "DATUM_REP": "determination:datetime",
        # 'OKRES_NAZE': 'admin:subdivision_code',
    }
    column_migrations = {"DATUM_REP": lambda col: pd.to_datetime(col, format="%d.%m.%Y")}
    extensions = {"https://fiboa.github.io/crop-extension/v0.2.0/schema.yaml"}
    column_additions = {"crop:code_list": ec_url("cz_2023.csv")}
    missing_schemas = {
        "properties": {
            "block_id": {"type": "string"},
        }
    }
