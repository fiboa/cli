import pandas as pd
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    sources = "https://download.inspire.ruokavirasto-awsa.com/data/2023/LandUse.ExistingLandUse.GSAAAgriculturalParcel.gpkg"
    id = "fi"
    short_name = "Finland"
    title = "Finnish Crop Fields (Maatalousmaa)"
    description = """
The Finnish Food Authority (FFA) since 2020 produces spatial data sets,
more specifically in this context the "Field parcel register" and "Agricultural parcel containing spatial data".
A set called "Agricultural land: arable land, permanent grassland or permanent crop (land use)".
    """
    provider = "Finnish Food Authority <https://www.ruokavirasto.fi/en/about-us/open-information/spatial-data-sets/>"
    attribution = "Finnish Food Authority"
    license = "CC-BY-4.0"
    # A peruslohko (basic parcel) is the reference parcel and holds one or more
    # kasvulohko, the growing parcels this dataset describes: PERUSLOHKOTUNNUS
    # repeats once per growing parcel (91 distinct over 100 sampled rows), so the
    # field is identified by the pair, and the basic parcel is the block.
    columns = {
        "geometry": "geometry",
        "id": "id",
        "PERUSLOHKOTUNNUS": "block_id",
        "area": "metrics:area",
        "VUOSI": "determination:datetime",
        "KASVIKOODI": "crop:code",
        "KASVIKOODI_SELITE_FI": "crop:name",
    }
    column_migrations = {
        # Make year (1st January) from column "VUOSI"
        "VUOSI": lambda col: pd.to_datetime(col, format="%Y"),
    }

    def migrate(self, gdf):
        gdf["id"] = gdf["PERUSLOHKOTUNNUS"].astype(str) + ":" + gdf["LOHKONUMERO"].astype(str)
        return super().migrate(gdf)

    ec_mapping_csv = "https://fiboa.org/code/fi/fi_2023.csv"

    area_is_in_ha = False
    area_calculate_missing = True

    missing_schemas = {
        "properties": {
            # PERUSLOHKOTUNNUS keeps its leading zeros ("0040000372")
            "block_id": {"type": "string"},
        }
    }
