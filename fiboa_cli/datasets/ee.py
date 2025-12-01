import pandas as pd

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin

COLUMNS = {
    "geometry": "geometry",
    "pollu_id": "id",
    "taotlusaasta": "determination:datetime",  # year
    "pindala_ha": "metrics:area",  # area (in ha)
    "taotletud_kultuur": "crop:name",  # requested crop culture
}
ATTRIBUTES = ",".join(["geom" if k == "geometry" else k for k in COLUMNS.keys()])


class Convert(AddHCATMixin, FiboaBaseConverter):
    variants = {
        str(
            year
        ): f"https://kls.pria.ee/geoserver/inspire_gsaa/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName=inspire_gsaa:LU.GSAA.AGRICULTURAL_PARCELS_{year}&propertyName={ATTRIBUTES}"
        for year in range(2024, 2009, -1)
    }
    ec_mapping_csv = "https://fiboa.org/code/ee/ee.csv"
    id = "ee"
    short_name = "Estonia"
    title = "Field boundaries for Estonia"
    description = """
Geospatial Aid Application Estonia Agricultural parcels.
The original dataset is provided by ARIB and obtained from the INSPIRE theme GSAA (specifically Geospaial Aid Application Estonia Agricultural parcels) through which the data layer Fields and Eco Areas (GSAA) is made available.
The data comes from ARIB's database of agricultural parcels.
    """
    provider = "Põllumajanduse Registrite ja Informatsiooni Amet <http://data.europa.eu/88u/dataset/pria-pollud>"
    attribution = "© Põllumajanduse Registrite ja Informatsiooni Amet"
    license = "CC-BY-SA-3.0"
    columns = COLUMNS
    column_migrations = {"taotlusaasta": lambda col: pd.to_datetime(col, format="%Y")}

    def file_migration(self, gdf, path: str, uri: str, layer=None):
        return gdf.set_crs(3301)
