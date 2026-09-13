import pandas as pd

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin

COLUMNS = {
    "geometry": "geometry",
    "id": "id",
    "pollu_id": "parcel_id",
    "taotlusaasta": "determination:datetime",  # year
    "pindala_ha": "metrics:area",  # area (in ha)
    "taotletud_kultuur": "crop:name",  # requested crop culture
    "taotletud_maakasutus": "land_use",  # requested land use: arable, permanent grassland, restored grassland
}
ATTRIBUTES = ",".join(
    "geom" if k == "geometry" else k for k in COLUMNS if k not in ("id", "parcel_id")
)


class Convert(AddHCATMixin, FiboaBaseConverter):
    # explicit cache names: the WFS URL has no usable file name
    variants = {
        str(year): {
            f"https://kls.pria.ee/geoserver/inspire_gsaa/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName=inspire_gsaa:LU.GSAA.AGRICULTURAL_PARCELS_{year}&propertyName={ATTRIBUTES}": f"ee_gsaa_{year}.gml"
        }
        # the WFS also lists layers for 2010-2015, but they return zero
        # features (checked 2026-08-30)
        for year in range(2024, 2015, -1)
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
    # The source publishes no crop code at all — the crop is free text, which is
    # what hcat:code is derived from — so this is the only classification it has.
    missing_schemas = {
        "properties": {
            "land_use": {"type": "string"},
            "parcel_id": {"type": "int64"},
        }
    }

    # PRIA's parcel id repeats in a few rows of some editions — 16 of the
    # 165,244 in 2016, one of them seven times — so it is published as
    # parcel_id, and the row index identifies the field in an edition where it
    # repeats. Safe, because an edition is one layer of one file.
    def migrate(self, gdf):
        if gdf["pollu_id"].is_unique:
            gdf["id"] = gdf["pollu_id"]
        else:
            repeats = len(gdf) - gdf["pollu_id"].nunique()
            self.warning(
                f"pollu_id repeats for {repeats:,} of {len(gdf):,} rows in this edition; "
                "numbering the rows and keeping it as parcel_id"
            )
            gdf["id"] = gdf.index
        return super().migrate(gdf)

    column_migrations = {"taotlusaasta": lambda col: pd.to_datetime(col, format="%Y")}

    def file_migration(self, gdf, path: str, uri: str, layer=None):
        return gdf.set_crs(3301)
