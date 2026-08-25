import re
from urllib.parse import urlencode

import pandas as pd
import requests
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.convert_gml import gml_assure_columns
from ..conversion.fiboa_converter import FiboaBaseConverter

BASE_URL = "https://gdiserv.bayern.de/srv66381/services/invekos_lpis-wfs"
PARAMS = {
    "service": "WFS",
    "version": "2.0.0",
    "request": "GetFeature",
    "typeNames": "lpis:AgriculturalArea",
}
# Server-enforced maximum. Larger values are silently capped, so paging must use this number.
PAGE_SIZE = 10_000


class DEBYBlockConverter(AdminConverterMixin, FiboaBaseConverter):
    id = "de_by_block"
    admin_subdivision_code = "BY"
    short_name = "Germany, Bavaria (LPIS)"
    title = "Field blocks for Bavaria, Germany"
    description = """
This dataset contains the field blocks ("Feldstücke") of Bavaria, the reference parcels of its Land
Parcel Identification System (LPIS). A Feldstück is a contiguous agricultural area belonging to a
single farm operator; areas separated by roads, tracks or watercourses are not combined, and
differing tenure, use or fertiliser planning do not split one. Delineation follows the area eligible
for support, which comprises agricultural area, agriculturally usable area and eligible landscape
elements. The data is published in the "IACS in INSPIRE" (TG2) data model and republished twice a
year for the application procedure.
"""

    provider = "Bayerisches Staatsministerium für Ernährung, Landwirtschaft, Forsten und Tourismus <https://www.stmelf.bayern.de>"
    attribution = "© Bayerisches Staatsministerium für Ernährung, Landwirtschaft, Forsten und Tourismus, CC BY 4.0"
    license = "CC-BY-4.0"

    extensions = {"https://fiboa.org/flik-extension/v0.2.0/schema.yaml"}

    # The service publishes no area attribute, so it is derived from the geometry. The data is in
    # EPSG:25832, so the result is already in m² and must not be scaled.
    area_is_in_ha = False
    area_calculate_missing = True

    columns = {
        "geometry": "geometry",
        "flik": ("flik", "id"),  # derived in migrate(); unique, unlike in Baden-Württemberg
        "agricultural_area_type": "agricultural_area_type",  # added in file_migration()
        "validFrom": "determination:datetime",
        "area": "metrics:area",  # not in the source; created by area_calculate_missing
    }
    column_migrations = {"validFrom": lambda col: pd.to_datetime(col)}

    missing_schemas = {
        "properties": {
            "agricultural_area_type": {
                "type": "string",
                "enum": ["Arable land", "Permanent grassland", "Permanent crop", "Other"],
            }
        }
    }

    def get_urls(self):
        # numberReturned is always reported as 0 by this server, so the page count has to come
        # from a hits request rather than from the responses themselves.
        hits = requests.get(BASE_URL, params={**PARAMS, "resultType": "hits"})
        hits.raise_for_status()
        total = int(re.search(r'numberMatched="(\d+)"', hits.text).group(1))

        query = urlencode({**PARAMS, "count": PAGE_SIZE})
        return {
            f"{BASE_URL}?{query}&startIndex={start}": f"de_by_block_{start}.gml"
            for start in range(0, total, PAGE_SIZE)
        }

    def file_migration(self, gdf, path, uri, layer=None):
        # The land cover class is carried as an xlink attribute, which the GML driver does not
        # guess into its generated schema, so ask for it explicitly.
        return gml_assure_columns(
            gdf,
            path,
            uri,
            layer,
            agricultural_area_type={
                "ElementPath": "agriculturalAreaType@title",
                "Type": "String",
                "Width": 255,
            },
        )

    def migrate(self, gdf):
        # The FLIK is the last dot-separated segment of the identifier URI, e.g.
        # https://registry.gdi-de.org/id/de.by.inspire.invekos.lpis.aa.DEBYLI9412000570
        gdf["flik"] = gdf["id"].str.rsplit(".", n=1).str[-1]
        return super().migrate(gdf)
