from .commons.admin import AdminConverterMixin
from .commons.ec import ec_url
from ..convert_utils import BaseConverter
import geopandas as gpd

class DKConverter(AdminConverterMixin, BaseConverter):
    years = {
        year: f"https://landbrugsgeodata.fvm.dk/Download/Marker/Marker_{year}.zip"
        for year in range(2024, 2008-1, -1)
    }
    id = "dk"
    short_name = "Denmark"
    title = "Denmark Crop Fields (Marker)"
    description = "The Danish Ministry of Food, Agriculture and Fisheries publishes Crop Fields (Marker) for each year."

    extensions = ["https://fiboa.github.io/crop-extension/v0.1.0/schema.yaml"]
    column_additions = {"crop:code_list": ec_url("nl_2020.csv")}

    providers = [
        {
            "name": "Ministry of Food, Agriculture and Fisheries of Denmark",
            "url": "https://fvm.dk/",
            "roles": ["licensor"]
        },
        {
            "name": "Danish Agricultural Agency",
            "url": "https://lbst.dk/",
            "roles": ["producer", "licensor"]
        }
    ]

    license = "CC-0"
    columns = {
        'geometry': 'geometry',
        'Marknr': 'id',
        'IMK_areal': "area",
        'Afgkode': 'crop:code',
        'Afgroede': 'crop:name',
    }

    def migrate(self, gdf) -> gpd.GeoDataFrame:
        gdf["determination_datetime"] = f"{self.year}-01-01T00:00:00Z"
        return gdf
