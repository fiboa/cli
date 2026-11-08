import pandas as pd
from vecorel_cli.conversion.admin import AdminConverterMixin

from ...conversion.fiboa_converter import FiboaBaseConverter
from .hcat import AddHCATMixin

DOCS = "https://ecass-project-documentation.readthedocs.io/en/latest/modules/data_access.html"


def drive_url(file_id):
    """A login-free download URL for a file in a public Google Drive folder"""
    return f"https://drive.usercontent.google.com/download?id={file_id}&export=download"


def to_date(col):
    # Kenya mixes ISO dates (2021-07-29) with US ones (1/22/2022)
    return pd.to_datetime(col, format="mixed").dt.date


class EcaasConverter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    """Crop-cut plots of the Bird's-Eye project (ECAAS), one converter per country"""

    description = """
Farm polygons from crop-cutting experiments of the Bird's-Eye project, a collaboration between Pula
and Tetra Tech under the Enabling Crop Analytics at Scale (ECAAS) project, funded by the Bill &
Melinda Gates Foundation. Enumerators visited smallholder farms, walked the boundary of the crop in
question with a GPS device and placed harvest boxes (mostly 8 by 5 m) inside it; the boxes were
harvested and weighed (kg) and the weight converted to a yield per hectare. Geospatial experts then
checked the polygons against satellite imagery and corrected those that did not fit the farm.
The polygons are a sample of farms, not a wall-to-wall map. Each one carries the crop, the planting
and harvest dates, the season, the crop condition at box placement, whether and with what the crop
was intercropped, and the harvested weight and yield.
    """
    provider = f"Pula Advisors <{DOCS}>"
    attribution = (
        "Pula Advisors and Tetra Tech, Bird's-Eye project, Enabling Crop Analytics at Scale (ECAAS)"
    )
    license = "GPL-2.0-or-later"

    columns = {
        "geometry": "geometry",
        "Case_ID": "id",
        # the name is the only identifier the source has for a crop
        "Crop_Type": ["crop:code", "crop:name"],
        "Planting_Date": "planting_date",
        "Harvesting_date": "harvest_date",
        "season": "season",
        "crop_condition": "crop_condition",
        "Intercropping": "intercropped",
        "inter_with_which_crop": "intercrop",
        "ADM1": "admin_level_1",
        "ADM2": "admin_level_2",
        "Final_Weight": "harvest_weight",
        "Yield(Mt/ha)": "yield",
    }
    # One Kenyan plot has no crop recorded
    column_filters = {"Crop_Type": lambda col: col.notna()}
    column_migrations = {
        "Planting_Date": to_date,
        "Harvesting_date": to_date,
        "Intercropping": lambda col: col.map({"yes": True, "no": False}).astype("boolean"),
    }

    missing_schemas = {
        "properties": {
            "planting_date": {"type": "date"},
            "harvest_date": {"type": "date"},
            "season": {"type": "string"},
            "crop_condition": {
                "type": "string",
                "description": "The state of the crop when the harvest boxes were placed",
            },
            "intercropped": {"type": "boolean"},
            "intercrop": {
                "type": "string",
                "description": "The crop(s) an intercropped field shares with its main crop",
            },
            "admin_level_1": {"type": "string"},
            "admin_level_2": {"type": "string"},
            "harvest_weight": {
                "type": "double",
                "description": "The weight harvested from the crop-cut boxes, in kg",
            },
            "yield": {
                "type": "double",
                "description": "The yield in tonnes per hectare, from the harvested weight",
            },
        }
    }
