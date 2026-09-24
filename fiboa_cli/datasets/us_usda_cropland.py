import pandas as pd
from loguru import logger
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import load_ec_mapping
from .commons.hcat import AddHCATMixin


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    # One archive carries the whole sequence: CSB1724.gdb has a CDL<year> crop
    # column for every year 2017-2024, so every variant reads the same source.
    variants = {
        str(y): {
            "https://www.nass.usda.gov/Research_and_Science/Crop-Sequence-Boundaries/datasets/NationalCSB_2017-2024_rev23.zip": [
                "NationalCSB_2017-2024_rev23/CSB1724.gdb"
            ]
        }
        for y in range(2024, 2016, -1)
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
    # The dissolve below merges adjacent CSB polygons of one crop and splits the
    # result again, so an output field is not a source CSB and `CSBID`, kept by
    # `aggfunc="first"`, names an arbitrary member of the group: it gave 3,093
    # distinct ids to 7.5 million fields. The county is part of the dissolve key,
    # so it does hold for every field the group produces.
    columns = {
        "geometry": "geometry",
        # "CDL2023": "crop:code", will be added in migrate
        "crop:name": "crop:name",
        "CNTY": "administrative_area_level_2",
        "CNTYFIPS": "administrative_area_level_2_code",
    }
    missing_schemas = {
        "properties": {
            "administrative_area_level_2": {"type": "string"},
            "administrative_area_level_2_code": {"type": "string"},
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
            # County is in the key so it stays true of every field: a group spans one
            # county, and a dissolve on attributes never cuts a source polygon, it only
            # declines to merge across the line. In Delaware that is 13 fields in 14,308.
            df = df.dissolve(by=[crop_key, "CNTYFIPS"], aggfunc="first", as_index=False).explode()
            gdfs.append(df)
        gdf = pd.concat(gdfs)
        del gdfs
        if self.ec_mapping is None:
            self.ec_mapping = load_ec_mapping(self.ec_mapping_csv, url=self.mapping_file)
        original_name_mapping = {
            int(e["original_code"]): e["original_name"] for e in self.ec_mapping
        }
        gdf["crop:name"] = gdf[crop_key].map(original_name_mapping)

        # nothing from the source identifies the dissolved fields; the base numbers them
        return gdf
