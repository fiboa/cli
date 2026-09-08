import re
from urllib.parse import urlencode

import pandas as pd
import requests
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter

BASE_URL = "https://geoservices6.civis.bz.it/geoserver/p_bz-Agriculture/ows"
LAYER = "p_bz-Agriculture:Fields-Used"
# The service caps a response at 110000 features; 50000 stays well inside that.
PAGE_SIZE = 50_000


class ITBZConverter(AdminConverterMixin, FiboaBaseConverter):
    id = "it_bz"
    admin_subdivision_code = "BZ"
    short_name = "Italy, South Tyrol"
    title = "Field boundaries for South Tyrol, Italy"
    description = """
The utilised agricultural area of South Tyrol, the autonomous Italian province of Bolzano, held in
the province's LAFIS system. The polygons are digitised manually from orthophotos or GPS survey and
aggregated by crop type, crop protection and crop-type detail, so a feature is an area of one crop
type rather than one farmer's application parcel. The source carries no farm or parcel identifier.
"""

    provider = "Autonome Provinz Bozen - Südtirol <https://agricoltura.provincia.bz.it/it/home>"
    attribution = "© Autonome Provinz Bozen - Südtirol"
    license = "CC0-1.0"

    extensions = {"https://fiboa.org/crop-extension/v0.2.0/schema.yaml"}
    column_additions = {"crop:code_list": "https://fiboa.org/code/it/bz/crop.csv"}

    columns = {
        "geometry": "geometry",
        "ID": "id",
        "CODE": "crop:code",
        # The province is bilingual; the feature type declares the Italian name first.
        "DESCRIPTION_IT": "crop:name",
        "AREA": "metrics:area",
        "BEGIN_DATE": "determination:datetime",
    }
    # AREA is already in m², like metrics:area, so it must not be scaled.
    area_is_in_ha = False
    column_migrations = {
        "BEGIN_DATE": lambda col: pd.to_datetime(col, format="%Y-%m-%dZ", utc=True),
    }

    def get_urls(self):
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeNames": LAYER,
            "outputFormat": "application/json",
        }
        # Derive the page count from the server instead of hardcoding it, so a changed layer
        # neither drops the tail nor requests empty pages.
        hits = requests.get(BASE_URL, params={**params, "resultType": "hits"})
        hits.raise_for_status()
        total = int(re.search(r'numberMatched="(\d+)"', hits.text).group(1))

        query = urlencode({**params, "count": PAGE_SIZE})
        return {
            f"{BASE_URL}?{query}&startIndex={start}": f"it_bz_{start}.json"
            for start in range(0, total, PAGE_SIZE)
        }

    def file_migration(self, gdf, path, uri, layer=None):
        # read_geojson hardcodes crs="EPSG:4326"; the service delivers EPSG:25832.
        return gdf.set_crs("EPSG:25832", allow_override=True)

    def migrate(self, gdf):
        # read_geojson injects its own "id" column from the GeoJSON feature id.
        # Drop it so renaming ID -> id does not create two columns called "id".
        return super().migrate(gdf.drop(columns=["id"]))
