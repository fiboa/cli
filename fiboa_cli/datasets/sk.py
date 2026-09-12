import re

from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin, load_ec_mapping

BASE = "https://data.slovensko.sk/download?id={}&blocksize=0"
# "Hranice užívania <year> shp" on https://data.slovensko.sk, one dataset per
# campaign. The portal also publishes 2016 and 2017, but those two are 7-Zip
# archives, which the downloader cannot extract.
ITEMS = {
    2026: "5a88fa63-04d7-4496-93ce-796f553a6478",
    2025: "56f934e9-3c6b-48c6-9115-cac418b4bb41",
    2024: "16daebac-f974-4002-81ee-053e10d1e2a3",
    2023: "f90f29e6-e222-432e-a4ef-c97cc1c5fb61",
    2022: "68f005a1-49d3-47ac-9717-a533c3a0508e",
    2021: "97d82440-b904-4671-8a24-2dc5b13a61f5",
    2020: "adc9765b-6ce4-43b2-9d31-263a740dd779",
    2019: "b0b42cfc-7605-4fb9-82db-fee913d09230",
    2018: "a6773bee-ec27-4626-b5fb-8bbfc7765cee",
}


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    variants = {str(year): {BASE.format(item): ["**/*.shp"]} for year, item in ITEMS.items()}
    id = "sk"
    short_name = "Slovakia"
    title = "Slovakia Agricultural Land Identification System"
    description = """
Systém identifikácie poľnohospodárskych pozemkov (LPIS)

LPIS is an agricultural land identification system. It represents the vector boundaries of agricultural land
and carries information about the unique code, acreage, culture/land use, etc., which is used as a reference
for farmers' applications, for administrative and cross-checks, on-site checks and also checks using remote
sensing methods.

Dataset Hranice užívania contains the use declared by applicants for direct support.
    """
    provider = "Pôdohospodárska platobná agentúra <https://www.apa.sk>"
    license = "CC0-1.0"  # "Open Data"
    ec_mapping_csv = "https://fiboa.org/code/sk/sk.csv"
    # KODKD is the LPIS block code, shared by several fields and sometimes empty;
    # the row index is the field id and the code is kept as block_id.
    index_as_id = True
    # The archives carry the date they were extracted, not one per field, so the
    # campaign the edition belongs to is the best date there is.
    use_variant_as_determination = True
    columns = {
        "id": "id",
        "geometry": "geometry",
        "KODKD": "block_id",
        "PLODINA": "crop:name",
        "KULTURA_NA": "crop_group",
        "LOKALITA_N": "municipality",
        "VYMERA": "metrics:area",
    }
    # The 2018 release names three of its columns differently, and every release
    # up to 2021 (and 2025) writes the crop in PLODINA_NA rather than PLODINA.
    OLD_SCHEMA = {"KDIEL": "KODKD", "VYMERA_KD": "VYMERA", "PLODINA_NA": "PLODINA"}
    missing_schemas = {
        "properties": {
            "block_id": {"type": "string"},
            "crop_group": {"type": "string"},
            "municipality": {"type": "string"},
        }
    }

    def migrate(self, gdf):
        gdf = gdf.rename(columns={k: v for k, v in self.OLD_SCHEMA.items() if k in gdf.columns})
        if self.ec_mapping is None:
            self.ec_mapping = load_ec_mapping(self.ec_mapping_csv, url=self.mapping_file)
            for row in self.ec_mapping:
                row["original_name"] = self._normalize(row["original_name"])
        # The register writes a no-break space in the three grassland names, so
        # they match nothing in the table: 102,835 fields of 2018-2024 that the
        # mapping does have a row for.
        gdf["PLODINA"] = gdf["PLODINA"].map(self._normalize)
        return super().migrate(gdf)

    @staticmethod
    def _normalize(value):
        if not isinstance(value, str):
            return value
        return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()
