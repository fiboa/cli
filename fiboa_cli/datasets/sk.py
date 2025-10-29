from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin, load_ec_mapping


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    sources = {
        "https://data.slovensko.sk/download?id=e39ad227-1899-4cff-b7c8-734f90aa0b59&blocksize=0": [
            "HU2024_20240917shp/HU2024_20240917.shp"
        ]
    }
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
    ec_mapping_csv = "sk_2021.csv"
    columns = {
        "geometry": "geometry",
        "KODKD": "id",
        "PLODINA": "crop:name",
        "KULTURA_NA": "crop_group",
        "LOKALITA_N": "municipality",
        "VYMERA": "metrics:area",
    }
    missing_schemas = {
        "properties": {
            "crop_group": {"type": "string"},
            "municipality": {"type": "string"},
        }
    }

    def migrate(self, gdf):
        if self.ec_mapping is None:
            self.ec_mapping = load_ec_mapping(self.ec_mapping_csv, url=self.mapping_file)
        mapping = {row["original_name"]: index + 1 for index, row in enumerate(self.ec_mapping)}
        gdf["crop:code"] = gdf["PLODINA"].map(mapping)
        return super().migrate(gdf)
