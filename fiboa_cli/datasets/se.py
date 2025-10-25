import pandas as pd
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    variants = {
        "2024": {
            "http://epub.sjv.se/inspire/inspire/wfs?SERVICE=WFS%20&REQUEST=GetFeature%20&VERSION=1.0.0%20&TYPENAMES=inspire:arslager_skifte%20&outputFormat=shape-zip%20&CQL_FILTER=arslager=%272024%27%20%20and%20geom%20is%20not%20null%20&format_options=CHARSET:UTF-8": "se2024.zip"
        },
        "2023": {
            "http://epub.sjv.se/inspire/inspire/wfs?SERVICE=WFS%20&REQUEST=GetFeature%20&VERSION=1.0.0%20&TYPENAMES=inspire:arslager_skifte%20&outputFormat=shape-zip%20&CQL_FILTER=arslager=%272023%27%20%20and%20geom%20is%20not%20null%20&format_options=CHARSET:UTF-8": "se2023.zip"
        },
    }
    id = "se"
    short_name = "Sweden"
    title = "Swedish Crop Fields (Jordbruksskiften)"
    description = """
    A crop field (Jordbruksskift) is a contiguous area of land within a block where a farmer grows a crop or otherwise manages the land.
    To receive compensation for agricultural support (EU support), farmers apply for support from the
    Swedish Agency for Agriculture via a SAM application. The data set contains parcels where the area
    applied for and the area decided on are the same. The data is published at the end of a year.
    """
    provider = "Jordbruksverket (The Swedish Board of Agriculture) <https://jordbruksverket.se>"
    attribution = "Jordbruksverket"
    license = "CC0-1.0"  # "Open Data"
    columns = {
        "geometry": "geometry",
        "id": "id",
        "faststalld": "metrics:area",
        "grdkod_mar": "crop:code",
        "arslager": "determination:datetime",
    }
    extensions = {"https://fiboa.org/crop-extension/v0.2.0/schema.yaml"}
    ec_mapping_csv = "se_2021.csv"
    column_migrations = {
        # Make year (1st January) from column "arslager"
        "arslager": lambda col: pd.to_datetime(col, format="%Y")
    }

    def migrate(self, gdf):
        gdf["id"] = gdf["blockid"] + "_" + gdf["skiftesbet"]
        return super().migrate(gdf)
