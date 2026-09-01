import re
from urllib.parse import urlencode

import requests
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.convert_gml import gml_assure_columns
from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.de_iacs import DEIACSMixin
from .de_sl import parse_flik, parse_size

BASE_URL = "https://geoportal.saarland.de/gdi-sl/inspirewfs_Bodenbedeckung_LPIS"
PARAMS = {
    "service": "WFS",
    "version": "2.0.0",
    "request": "GetFeature",
    "typeNames": "lcv:LandCoverUnit",
}
# The WFS accepts larger pages, but 2500 keeps each response around 7 MB. It is also the ceiling
# of the limit allowlist on the OGC API - Features endpoint for the same data.
PAGE_SIZE = 2500


class DESLBlockConverter(AdminConverterMixin, DEIACSMixin, FiboaBaseConverter):
    id = "de_sl_block"
    admin_subdivision_code = "SL"
    short_name = "Germany, Saarland (LPIS)"
    title = "Field blocks for Saarland, Germany"
    description = """
The reference parcels ("Referenzschläge") of the Saarland Land Parcel Identification System (LPIS),
the reference system for area-based agricultural payments. The data is transformed into the INSPIRE
"Land Cover" data model, so each parcel carries a land cover class from the national IACS code list
alongside its FLIK. The area given is the eligible parcel size recorded in InVeKoS, not the
geometric area of the polygon. The complementary application parcels ("Antragsschläge") are
published separately.
"""

    provider = "Ministerium für Umwelt, Klima, Mobilität, Agrar und Verbraucherschutz <https://geoportal.saarland.de/spatial-objects/384>"
    attribution = "© GDI-SL 2026, CC BY 4.0"
    license = "CC-BY-4.0"

    extensions = {"https://fiboa.org/flik-extension/v0.2.0/schema.yaml"}

    columns = {
        "geometry": "geometry",
        "flik": ("flik", "id"),  # derived in migrate(); unique
        "area_type": "crop:code",  # added in file_migration(), trimmed in migrate()
        "area": "metrics:area",  # derived in migrate(); in hectares
    }

    def get_urls(self):
        # numberReturned is always reported as 0 by this server, so the page count has to come
        # from a hits request rather than from the responses themselves.
        hits = requests.get(BASE_URL, params={**PARAMS, "resultType": "hits"})
        hits.raise_for_status()
        total = int(re.search(r'numberMatched="(\d+)"', hits.text).group(1))

        query = urlencode({**PARAMS, "count": PAGE_SIZE})
        return {
            f"{BASE_URL}?{query}&startIndex={start}": f"de_sl_block_{start}.gml"
            for start in range(0, total, PAGE_SIZE)
        }

    def file_migration(self, gdf, path, uri, layer=None):
        # The land cover class is a nested xlink attribute, which the GML driver does not guess
        # into its generated schema. GDAL separates the steps of an element path with "|".
        return gml_assure_columns(
            gdf,
            path,
            uri,
            layer,
            area_type={
                "ElementPath": "landCoverObservation|LandCoverObservation|class@href",
                "Type": "String",
                "Width": 255,
            },
        )

    def migrate(self, gdf):
        # The FLIK and the size are both encoded in the INSPIRE description, e.g.
        # "Size in ha: 0.11206, flik: DESLLI0000248744"
        gdf["flik"] = gdf["description"].apply(parse_flik)
        gdf["area"] = gdf["description"].apply(parse_size)
        # …/codelist/de.iacs/AgriculturalAreaTypeValue/GL -> GL
        gdf["area_type"] = gdf["area_type"].str.rsplit("/", n=1).str[-1]
        return super().migrate(gdf)
