import pandas as pd
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.converter_wfs import WFSConverterMixin
from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.de_iacs import DEIACSMixin

BASE_URL = "https://inspire-geo.ibykus.net/geoserver/lawi/wfs"


class DEHEConverter(AdminConverterMixin, DEIACSMixin, WFSConverterMixin, FiboaBaseConverter):
    id = "de_he"
    admin_subdivision_code = "HE"
    short_name = "Germany, Hesse"
    title = "Field blocks for Hesse, Germany"
    description = """
The reference parcel is the basic spatial unit for administering and geographically locating
agricultural parcels in Hesse. One reference parcel may contain several parcels declared under
InVeKoS and may be farmed by one or more farmers or producer associations. The data belongs to the
system for identifying agricultural parcels (LPIS), a subsystem of the Integrated Administration and
Control System (IACS) under Article 68 of Regulation (EC) No 1306/2013.
"""

    provider = "Land Hessen <https://www.geoportal.hessen.de/spatial-objects/886>"
    attribution = "© Land Hessen, CC BY 4.0"
    license = "CC-BY-4.0"

    extensions = {"https://fiboa.org/flik-extension/v0.2.0/schema.yaml"}

    variants = {str(year): str(year) for year in range(2025, 2022, -1)}

    wfs_url = BASE_URL
    wfs_page_size = 25_000
    wfs_extension = "json"

    # 2023 and 2024 publish no area, and the declaredArea 2025 does publish is the area of
    # the polygon to three decimals, so every edition measures it: EPSG:25832, already m2.
    area_is_in_ha = False
    area_calculate_missing = True

    columns = {
        "geometry": "geometry",
        "flik": "flik",  # derived in migrate()
        "id": "id",  # the flik
        "agriculturalAreaType": "crop:code",  # de.iacs codes; agriculturalAreaType_txt is the label
        "validFrom": "determination:datetime",
    }
    column_migrations = {"validFrom": lambda col: pd.to_datetime(col, format="%d.%m.%Y")}

    def get_wfs_params(self):
        return {
            "typeNames": f"lawi:LPIS-Referenzparzellen {self.variant}",
            "outputFormat": "application/json",
        }

    def file_migration(self, gdf, path, uri, layer=None):
        # read_geojson hardcodes crs="EPSG:4326"; the service delivers EPSG:25832.
        return gdf.set_crs("EPSG:25832", allow_override=True)

    def migrate(self, gdf):
        # The 2023 and 2024 layers put the id in ID, beside the driver's own feature id,
        # and carry no land cover class.
        gdf["id"] = gdf.get("ID", gdf["id"])
        gdf["agriculturalAreaType"] = gdf.get("agriculturalAreaType")

        # The FLIK is the last dot-separated segment of the id, e.g.
        # DE.HE.RP.DEHELI0004994212 -> DEHELI0004994212
        gdf["flik"] = gdf["id"].str.rsplit(".", n=1).str[-1].astype("string")
        gdf["id"] = gdf["flik"]
        return super().migrate(gdf)

    def get_columns(self, gdf):
        columns = super().get_columns(gdf)
        if gdf["agriculturalAreaType"].isna().all():
            # ship no crop column at all, rather than one that is empty in every row
            columns = {k: v for k, v in columns.items() if not str(v).startswith("crop:")}
        return columns
