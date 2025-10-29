from geopandas import GeoDataFrame
from vecorel_cli.conversion.admin import AdminConverterMixin

from fiboa_cli.conversion.fiboa_converter import FiboaBaseConverter
from fiboa_cli.datasets.commons.data import read_data_csv


class BGConverter(AdminConverterMixin, FiboaBaseConverter):
    sources = {
        "http://inspire.mzh.government.bg:8080/geoserver/ows?request=GetFeature&service=WFS&version=2.0.0&outputFormat=SHAPE-ZIP&typeNames=VectorDataSet:Arable_Land_2024": "bg_arable_land_2024.zip"
    }

    id = "bg"
    short_name = "Bulgaria"
    title = "Bulgaria"
    license = "CC-BY-4.0"
    provider = "Ministry of Health"
    description = """\
    Bulgarian Agriculture areas. Dataset has been produced from field checks and orthophotos mapping.
    Categorized in Arable Land, Greenhouses, Mixed Land Use and Rice fields.
    """

    area_is_in_ha = False
    columns = {
        "geometry": "geometry",
        "PHBIDENT": "id",
        "USAGEENG": "crop:name",
        "crop:code": "crop:code",
        "AREA": "metrics:area",
    }
    extensions = {"https://fiboa.org/crop-extension/v0.2.0/schema.yaml"}
    column_additions = {"crop:code_list": "https://fiboa.org/code/bg/bg_arable.csv"}

    def migrate(self, gdf) -> GeoDataFrame:
        gdf = super().migrate(gdf)
        csv = read_data_csv("bg_arable.csv")
        crop_to_code = {e["original_name"]: i + 1 for i, e in enumerate(csv)}
        gdf["crop:code"] = gdf["USAGEENG"].map(crop_to_code)
        return gdf
