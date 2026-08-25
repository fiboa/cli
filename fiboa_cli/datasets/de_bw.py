import re

import pandas as pd
import requests
from urllib.parse import urlencode
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter

BASE_URL = "https://owsproxy.lgl-bw.de/owsproxy/wfs/WFS_LW-BW_GISELA_landw_Parzellen"
FARMLAND = "Bodenbedeckung IN ('Ackerland','Grünland','Dauerkultur')"


class DEBWConverter(AdminConverterMixin, FiboaBaseConverter):
    id = "de_bw"
    admin_subdivision_code = "BW"
    short_name = "Germany, Baden-Württemberg"
    title = "Field boundaries for Baden-Württemberg, Germany"
    description = """
GISELa is the Land Parcel Identification System (LPIS) of Baden-Württemberg, the reference system for
area-based agricultural payments. Unlike most German states, which use field blocks ("Feldblöcke"),
Baden-Württemberg uses the cadastral parcel ("Katasterflurstück") as its reference parcel, subdivided
by land cover ("Bodenbedeckung") - so the same FLIK can appear on several rows. This converter keeps
the agricultural classes (arable land, grassland, permanent crops) and drops landscape elements and
non-agricultural areas. The area given is the maximum area eligible for direct payments, not the
geometric area of the polygon.
"""

    provider = "Ministerium für Ländlichen Raum und Verbraucherschutz Baden-Württemberg <https://mlr.baden-wuerttemberg.de>"
    attribution = "© MLR Baden-Württemberg, dl-de/by-2-0"
    license = "DL-DE-BY-2.0"

    extensions = {"https://fiboa.org/flik-extension/v0.2.0/schema.yaml"}

    # One variant per published year, newest first -> 2022 is the default.
    variants = {str(year): str(year) for year in range(2022, 2017, -1)}

    page_size = 50_000

    columns = {
        "geometry": "geometry",
        "Geo-ID": "id",
        "FLIK": "flik",              # NOT the id: several rows share one FLIK
        "Bodenbedeckung": "bodenbedeckung",
        "FlaecheInHa": "metrics:area",
        "Antragsjahr": "determination:datetime",
    }
    column_migrations = {"Antragsjahr": lambda col: pd.to_datetime(col, format="%Y")}

    missing_schemas = {
        "properties": {
            "bodenbedeckung": {
                "type": "string",
                "enum": ["Ackerland", "Grünland", "Dauerkultur"],
            }
        }
    }

    def get_urls(self):
        latest = next(iter(self.variants))
        if not self.variant:
            self.variant = latest

        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeNames": f"lw:v_gisela_landw_parzellen_{self.variant}",
            "outputFormat": "application/json",
            "cql_filter": FARMLAND,
            # NO srsName: the server rounds to 4 decimals in the output CRS, so asking
            # for degrees would quantise coordinates to ~10 m. Fetch native, relabel below.
        }

        # One cheap request so the page list is derived from the server, not hardcoded.
        hits = requests.get(BASE_URL, params={**params, "resultType": "hits"})
        total = int(re.search(r'numberMatched="(\d+)"', hits.text).group(1))

        query = urlencode({**params, "count": self.page_size})
        return {
            f"{BASE_URL}?{query}&startIndex={start}": f"de_bw_{self.variant}_{start}.json"
            for start in range(0, total, self.page_size)
        }


    def file_migration(self, gdf, path, uri, layer=None):
        # read_geojson hardcodes crs="EPSG:4326"; the payload is really EPSG:25832.
        # allow_override is required because a CRS is already set.
        return gdf.set_crs("EPSG:25832", allow_override=True)

    def migrate(self, gdf):
        # read_geojson injects its own "id" column from the GML feature id.
        # Drop it so renaming Geo-ID -> id does not create two columns called "id".
        return super().migrate(gdf.drop(columns=["id"]))
