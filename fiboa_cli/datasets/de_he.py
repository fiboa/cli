import re
from urllib.parse import urlencode

import pandas as pd
import requests
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.de_iacs import DEIACSMixin

BASE_URL = "https://inspire-geo.ibykus.net/geoserver/lawi/wfs"
PAGE_SIZE = 25_000


class DEHEConverter(AdminConverterMixin, DEIACSMixin, FiboaBaseConverter):
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

    # Only the 2025 layer publishes a declared area, so the rest is measured from the geometry,
    # which is in EPSG:25832 and therefore already in m2.
    area_is_in_ha = False
    area_calculate_missing = True

    columns = {
        "geometry": "geometry",
        "flik": "flik",  # derived in migrate()
        "id": "id",  # the flik, plus a part number where a block is several polygons
        "agriculturalAreaType": "crop:code",  # de.iacs codes; agriculturalAreaType_txt is the label
        "declaredArea": "metrics:area",
        "validFrom": "determination:datetime",
    }
    column_migrations = {
        "validFrom": lambda col: pd.to_datetime(col, format="%d.%m.%Y"),
        "declaredArea": lambda col: col.astype(float) * 10_000,  # published in hectares
    }

    def get_urls(self):
        if not self.variant:
            self.variant = next(iter(self.variants))

        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeNames": f"lawi:LPIS-Referenzparzellen {self.variant}",
            "outputFormat": "application/json",
        }
        # Derive the page count from the server instead of hardcoding it, so a changed layer
        # neither drops the tail nor requests empty pages.
        hits = requests.get(BASE_URL, params={**params, "resultType": "hits"})
        hits.raise_for_status()
        total = int(re.search(r'numberMatched="(\d+)"', hits.text).group(1))

        query = urlencode({**params, "count": PAGE_SIZE})
        return {
            f"{BASE_URL}?{query}&startIndex={start}": f"de_he_{self.variant}_{start}.json"
            for start in range(0, total, PAGE_SIZE)
        }

    def file_migration(self, gdf, path, uri, layer=None):
        # read_geojson hardcodes crs="EPSG:4326"; the service delivers EPSG:25832.
        return gdf.set_crs("EPSG:25832", allow_override=True)

    def migrate(self, gdf):
        # The 2023 and 2024 layers put the id in ID, beside the driver's own feature id, and
        # carry neither a land cover class nor a declared area; a zero area is what
        # area_calculate_missing looks for.
        gdf["id"] = gdf.get("ID", gdf["id"])
        gdf["agriculturalAreaType"] = gdf.get("agriculturalAreaType")
        gdf["declaredArea"] = gdf.get("declaredArea", 0)

        # split here: the base converter explodes only after it has checked the ids
        gdf = self.split_multipart(gdf)

        # The FLIK is the last dot-separated segment of the id, e.g.
        # DE.HE.RP.DEHELI0004994212 -> DEHELI0004994212
        gdf["flik"] = gdf["id"].str.rsplit(".", n=1).str[-1].astype("string")

        # a handful of blocks are several polygons; only the id has to tell the parts apart
        gdf["id"] = gdf["flik"]
        part = gdf.groupby("id").cumcount()
        gdf.loc[part > 0, "id"] += "-" + (part[part > 0] + 1).astype("string")
        return super().migrate(gdf)

    def get_columns(self, gdf):
        columns = super().get_columns(gdf)
        if gdf["agriculturalAreaType"].isna().all():
            # ship no crop column at all, rather than one that is empty in every row
            columns = {k: v for k, v in columns.items() if not str(v).startswith("crop:")}
        return columns
