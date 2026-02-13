import pandas as pd
from loguru import logger
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import load_ec_mapping
from .commons.hcat import AddHCATMixin


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    variants = {
        "2024": {
            "https://www.nass.usda.gov/Research_and_Science/Crop-Sequence-Boundaries/datasets/NationalCSB_2017-2024_rev23.zip": [
                "NationalCSB_2017-2024_rev23/CSB1724.gdb"
            ]
        },
        "2023": {
            "https://www.nass.usda.gov/Research_and_Science/Crop-Sequence-Boundaries/datasets/NationalCSB_2016-2023_rev23.zip": [
                "NationalCSB_2016-2023_rev23/CSB1623.gdb"
            ]
        },
    }
    id = "us_usda_cropland"
    short_name = "US (USDA CSB)"
    title = "U.S. Department of Agriculture Crop Sequence Boundaries"
    description = """
The Crop Sequence Boundaries (CSB) developed with USDA's Economic Research Service, produces estimates of field boundaries, crop acreage, and crop rotations across the contiguous United States. It uses satellite imagery with other public data and is open source allowing users to conduct area and statistical analysis of planted U.S. commodities and provides insight on farmer cropping decisions.

NASS needed a representative field to predict crop planting based on common crop rotations such as corn-soy and ERS is using this product to study changes in farm management practices like tillage or cover cropping over time.

CSB represents non-confidential single crop field boundaries over a set time frame. It does not contain personal identifying information. The boundaries captured are of crops grown only, not ownership boundaries or tax parcels (unit of property). The data are from satellite imagery and publicly available data, it does not come from producers or agencies like the Farm Service Agency.
    """
    extensions = {"https://fiboa.org/crop-extension/v0.2.0/schema.yaml"}
    provider = "United States Department of Agriculture <https://www.nass.usda.gov>"
    license = "License and Liability <https://gee-community-catalog.org/projects/csb/#license-and-liability>"
    columns = {
        "geometry": "geometry",
        "CSBID": "id",
        "CDL2023": "crop:code",
        "crop:name": "crop:name",
        "CNTY": "administrative_area_level_2",
    }
    column_additions = {
        "determination:datetime": "2023-05-01T00:00:00Z",
    }
    missing_schemas = {
        "properties": {
            "administrative_area_level_2": {"type": "string"},
        }
    }
    ec_mapping_csv = "https://fiboa.org/code/us/usda/cropland.csv"

    def migrate(self, gdf):
        """
        Perform migration on the GeoDataFrame by dissolving polygons by crop code
        and mapping crop names.

        "dissolve": merge adjacent polygons with the same crop
        geodataframe.Dissolve(method="unary") is **slow** for large datasets
        So we're handling this huge dataset in blocks, states are a natural grouping-method
        """
        assert self.variant, "Variant must be set"
        crop_key = f"CDL{self.variant}"
        self.columns[crop_key] = "crop:code"

        gdf = super().migrate(gdf)
        states = list(gdf["STATEFIPS"].unique())
        gdfs = []
        for state in states:
            logger.info(f"Handling State {state}")
            df = gdf[gdf["STATEFIPS"] == state].explode()
            df = df.dissolve(by=[crop_key], aggfunc="first", as_index=False).explode()
            gdfs.append(df)
        gdf = pd.concat(gdfs)
        del gdfs
        if self.ec_mapping is None:
            self.ec_mapping = load_ec_mapping(self.ec_mapping_csv, url=self.mapping_file)
        original_name_mapping = {
            int(e["original_code"]): e["original_name"] for e in self.ec_mapping
        }
        gdf["crop:name"] = gdf[crop_key].map(original_name_mapping)
        return gdf
