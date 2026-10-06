from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin

BASE = "https://data.cnra.ca.gov/dataset/6c3d65e3-35bb-49e1-a51e-49d5a2cf09a9/resource"

# 2014 names its crops only; each name has one dominant code in 2016, which has both
CROP_CODE_BY_NAME = {
    "Alfalfa and Alfalfa Mixtures": "P1",
    "Almonds": "D12",
    "Apples": "D1",
    "Avocados": "C5",
    "Beans (Dry)": "F10",
    "Bush Berries": "T19",
    "Carrots": "T6",
    "Cherries": "D3",
    "Citrus": "C",
    "Cole Crops": "T4",
    "Corn, Sorghum and Sudan": "F16",
    "Cotton": "F1",
    "Dates": "C4",
    "Flowers, Nursery and Christmas Tree Farms": "T16",
    "Grapes": "V",
    "Greenhouse": "T27",
    "Idle": "X",
    "Kiwis": "C8",
    "Lettuce/Leafy Greens": "T8",
    "Managed Wetland": "NR",
    "Melons, Squash and Cucumbers": "T9",
    "Miscellaneous Deciduous": "D10",
    "Miscellaneous Field Crops": "F11",
    "Miscellaneous Grain and Hay": "G6",
    "Miscellaneous Grasses": "P6",
    "Miscellaneous Subtropical Fruits": "C7",
    "Miscellaneous Truck Crops": "T18",
    "Mixed Pasture": "P3",
    "Olives": "C6",
    "Onions and Garlic": "T10",
    "Peaches/Nectarines": "D5",
    "Pears": "D6",
    "Peppers": "T21",
    "Pistachios": "D14",
    "Plums, Prunes and Apricots": "D16",
    "Pomegranates": "D15",
    "Potatoes and Sweet Potatoes": "T31",
    "Rice": "R1",
    "Safflower": "F2",
    "Strawberries": "T20",
    "Sunflowers": "F12",
    "Tomatoes": "T15",
    "Urban": "U",
    "Walnuts": "D13",
    "Wheat": "G2",
    "Wild Rice": "R2",
    "Young Perennials": "YP",
}


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    variants = {
        "2024": {
            f"{BASE}/157956a5-507e-4c6c-b161-b21361488576/download/i15_crop_mapping_2024_provisional_20251208.gdb.zip": [
                "i15_Crop_Mapping_2024_Provisional_20251208.gdb"
            ]
        },
        "2023": {
            f"{BASE}/4e17ca38-268e-4bf5-bbc5-09636d44ed60/download/i15_crop_mapping_2023_final.gdb.zip": [
                "i15_Crop_Mapping_2023_Final.gdb"
            ]
        },
        "2022": {
            f"{BASE}/e41f74d2-7ff9-4871-bc95-1e9673fc53cb/download/i15_crop_mapping_2022.gdb.zip": [
                "i15_crop_mapping_2022.gdb"
            ]
        },
        "2021": {
            f"{BASE}/cd1ce211-ac75-44b4-9ea4-345ce2fd0548/download/i15_crop_mapping_2021_gdb.zip": [
                "i15_Crop_Mapping_2021_GDB/i15_Crop_Mapping_2021.gdb"
            ]
        },
        "2020": {
            f"{BASE}/44c1bde8-7ac4-4582-b8de-d09264e180fb/download/i15_crop_mapping_2020-gdb.zip": [
                "i15_Crop_Mapping_2020 GDB/i15_Crop_Mapping_2020.gdb"
            ]
        },
        "2019": {
            f"{BASE}/519a6ac2-77f5-4da6-85f3-ada74d7eddee/download/i15_crop_mapping_2019_gdb.zip": [
                "i15_Crop_Mapping_2019_GDB/i15_Crop_Mapping_2019.gdb"
            ]
        },
        "2018": {
            f"{BASE}/05dc698d-9587-453a-a494-a07beadbbe62/download/i15_crop_mapping_2018_gdb.zip": [
                "i15_Crop_Mapping_2018_GDB/i15_Crop_Mapping_2018.gdb"
            ]
        },
        "2016": {
            f"{BASE}/489d7ab8-f68a-45b4-8113-bb89bc4d9a9c/download/i15_crop_mapping_2016_gdb.zip": [
                "i15_Crop_Mapping_2016_GDB/i15_Crop_Mapping_2016.gdb"
            ]
        },
        "2014": {
            f"{BASE}/04f89c79-59d1-4981-a3ab-853fdbc79d37/download/i15_crop_mapping_2014_gdb.zip": [
                "i15_Crop_Mapping_2014_GDB/i15_Crop_Mapping_2014.gdb"
            ]
        },
    }
    id = "us_ca_scm"
    admin_subdivision_code = "CA"
    short_name = "US, California (SCM)"
    title = "California (US) Statewide Crop Mapping"
    description = """
For many years, the California Department of Water Resources (DWR) has collected land use data throughout the state
and used this information to develop water use estimates for statewide and regional planning efforts, including water
use projections, water use efficiency evaluation, groundwater model development, and water transfers. The statewide
crop maps are made from remote sensing by Land IQ under contract to DWR. 2024 is provisional.
    """
    provider = "California Department of Water Resources <https://data.cnra.ca.gov/dataset/statewide-crop-mapping>"
    attribution = "California Department of Water Resources, Statewide Crop Mapping"
    license = "CC0-1.0"
    columns = {
        "geometry": "geometry",
        "UniqueID": "id",
        "crop_code": "crop:code",
        "crop:name": "crop:name",
        "COUNTY": "admin_level_2",
        "determination:datetime": "determination:datetime",
    }
    hcat_mapping_csv = "https://fiboa.org/code/us/ca/scm.csv"
    missing_schemas = {
        "properties": {
            "admin_level_2": {"type": "string"},
        }
    }

    def migrate(self, gdf):
        gdf = super().migrate(gdf)
        # three generations of the schema: names (2014), seasons (2016, 2018), a main crop
        if "MAIN_CROP" in gdf.columns:
            gdf["crop_code"] = gdf["MAIN_CROP"]
        elif "CROPTYP2" in gdf.columns:
            gdf["crop_code"] = gdf["CROPTYP2"]
        else:
            gdf["crop_code"] = gdf[f"Crop{self.variant}"].map(CROP_CODE_BY_NAME)
        gdf["crop:name"] = gdf["crop_code"].map(self.hcat_lookup("original_code", "original_name"))
        if "County" in gdf.columns:
            gdf = gdf.rename(columns={"County": "COUNTY"})
        gdf["determination:datetime"] = f"{self.variant}-07-01T00:00:00Z"
        return gdf
