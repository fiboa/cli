import geopandas as gpd
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import ec_url


class DKConverter(AdminConverterMixin, FiboaBaseConverter):
    variants = {
        str(variant): f"https://landbrugsgeodata.fvm.dk/Download/Marker/Marker_{variant}.zip"
        for variant in range(2024, 2008 - 1, -1)
    }
    id = "dk"
    short_name = "Denmark"
    title = "Denmark Crop Fields (Marker)"
    description = "The Danish Ministry of Food, Agriculture and Fisheries publishes Crop Fields (Marker) for each year."

    extensions = {"https://fiboa.org/crop-extension/v0.2.0/schema.yaml"}
    column_additions = {"crop:code_list": ec_url("nl_2020.csv")}

    provider = "Danish Agricultural Agency <https://lbst.dk/>"

    license = "CC-0"
    columns = {
        "geometry": "geometry",
        "Marknr": "id",
        "IMK_areal": "metrics:area",
        "Afgkode": "crop:code",
        "Afgroede": "crop:name",
    }

    def migrate(self, gdf) -> gpd.GeoDataFrame:
        gdf["determination:datetime"] = f"{self.variant}-01-01T00:00:00Z"
        return gdf
