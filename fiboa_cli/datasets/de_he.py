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
    title = "Field boundaries for Hesse, Germany"
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

    columns = {
        "geometry": "geometry",
        "flik": ("flik", "id"),  # derived in migrate()
        "agriculturalAreaType": "crop:code",  # de.iacs codes; agriculturalAreaType_txt is the label
        "declaredArea": "metrics:area",  # in hectares, hence the area_is_in_ha default
        "validFrom": "determination:datetime",
    }
    column_migrations = {
        "validFrom": lambda col: pd.to_datetime(col, format="%d.%m.%Y"),
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
        # The FLIK is the last dot-separated segment of the id, e.g.
        # DE.HE.RP.DEHELI0004994212 -> DEHELI0004994212
        gdf["flik"] = gdf["id"].str.rsplit(".", n=1).str[-1]
        return super().migrate(gdf)
