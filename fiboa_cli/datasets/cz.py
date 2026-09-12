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
    # the 2026 archive nests the shapefile in a folder, older ones are flat
    variants = {str(k): {BASE.format(v): ["**/*.shp"]} for k, v in ITEMS.items()}
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

    # The GPZ_DP releases (2019-2022) name the same things differently, carry no
    # application date, and identify nothing per row: ENTITA_ID is the land block
    # and repeats per crop declared on it, 242,754 over the 282,462 rows of 2019.
    OLD_SCHEMA = {"PLODINA_NA": "PLOD_NAZE", "DEKL_VYMER": "ZAKRES_VYM"}

    # 2020 leaves PLODINA_ID empty in 98.1% of its rows and names the crop in the
    # ministry's vocabulary, not EuroCrops' botanical one ("Pšenice ozimá" against
    # "Pšenice setá ozimá"). This table has the code its neighbours give each name.
    crop_names_csv = "https://fiboa.org/code/cz/cz_crop_names.csv"

    def migrate(self, gdf):
        if "PLODINA_NA" in gdf.columns:
            gdf = gdf.rename(columns=self.OLD_SCHEMA)
            gdf["DPB_ID"] = gdf["ENTITA_ID"]
            # Positional: the index repeats when an edition ships two shapefiles.
            gdf["ZAKRES_ID"] = range(len(gdf))
            # No date in these releases; the edition is the campaign year.
            gdf["DATUM_REP"] = f"01.01.{self.variant}"
            codes = gdf["PLODINA_ID"].astype("string").str.strip()
            if codes.isna().any():
                by_name = gdf["PLOD_NAZE"].astype("string").str.strip().map(self._codes_by_name())
                gdf["PLODINA_ID"] = codes.fillna(by_name)
        elif gdf["ZAKRES_ID"].duplicated().any():
            # A declaration straddling two land blocks is listed once per block
            # with the same geometry both times (one pair in 2026). A repeat of
            # a different shape is something else and still fails the id check.
            repeats = gdf.assign(_wkb=gdf.geometry.to_wkb()).duplicated(["ZAKRES_ID", "_wkb"])
            self.info(f"Dropping {repeats.sum()} declaration(s) listed once per land block")
            gdf = gdf[~repeats]
        return super().migrate(gdf)

    def _codes_by_name(self) -> dict:
        from .commons.hcat import load_ec_mapping

        return {
            row["original_name"].strip(): row["original_code"].strip()
            for row in load_ec_mapping(self.crop_names_csv)
        }

    ec_mapping_csv = "cz_2023.csv"
    # EuroCrops mapped the 2023 code list. The 2019-2022 editions declare 120
    # codes it never saw — 11.4% of their rows, fallow and ware potatoes among
    # them — so their HCAT comes from a table of our own.
    ec_mapping_supplements = ["https://fiboa.org/code/cz/cz_supplement.csv"]
    missing_schemas = {
        "properties": {
            "block_id": {"type": "string"},
        }
    }
