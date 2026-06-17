import pandas as pd
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin

BASE = "https://agrigis.gov.cz/portal/sharing/rest/content/items/{}/data"
# Check data on https://agrigis.gov.cz/portal/apps/storymaps/stories/99ddc665f57a4843b878e86c23e99b31
ITEMS = {
    2026: "7bcdda9b19724faba447585683c4cfd1",
    2025: "2cac84bb1f5245598f0334c6011ef5a6",
    2024: "1b315e81ce474b3b808b4940808bb106",
    2023: "d9a6e306fe534a059519fdf788da1df6",
    2022: "791cd91c4f354c9085173fc267b2be4d",
    2021: "c662c15b70794a06937096be54c095ab",
    2020: "c843561778b44b308485aafdbb813d76",
    2019: "9cbc2b4429704b73863596fa5f488d27",
}


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    # see https://mze.gov.cz/public/app/eagriapp/lpisdata/
    variants = {str(k): {BASE.format(v): ["*.shp"]} for k, v in ITEMS.items()}
    id = "cz"
    short_name = "Czech"
    title = "Field boundaries for Czech"
    description = "The cropfields of Czech (Plodina)"
    provider = "Czech Ministry of Agriculture (Ministr Zemědělství) <https://mze.gov.cz/public/portal/mze/farmar/LPIS>"
    license = "CC0-1.0"
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
    ec_mapping_csv = "cz_2023.csv"
    missing_schemas = {
        "properties": {
            "block_id": {"type": "string"},
        }
    }
