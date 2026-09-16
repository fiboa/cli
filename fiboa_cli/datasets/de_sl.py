import re
from urllib.parse import urlencode

import requests
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter

BASE_URL = (
    "https://geoportal.saarland.de/gdi-sl/inspirewfs_Existierende_Bodennutzung_Antragsschlaege"
)
PARAMS = {
    "service": "WFS",
    "version": "2.0.0",
    "request": "GetFeature",
    "typeNames": "elu:ExistingLandUseObject",
    # The media type contains a ";", which has to be percent-encoded. Passed through raw, the
    # server reads the parameter as "application/gml+xml" and rejects it.
    "outputFormat": "application/gml+xml; version=3.2",
}
# The WFS accepts larger pages, but 2500 keeps each response around 8 MB.
PAGE_SIZE = 2500


class Converter(AdminConverterMixin, FiboaBaseConverter):
    id = "de_sl"
    admin_subdivision_code = "SL"
    short_name = "Germany, Saarland"
    title = "Field boundaries for Saarland, Germany"
    description = """This dataset contains data transformed into the INSPIRE data model “Land Use” of the IACS areas applied for within the framework of agricultural land promotion (GIS application) from the Saarland."""
    provider = "Ministerium für Umwelt, Klima, Mobilität, Agrar und Verbraucherschutz <https://geoportal.saarland.de>"
    attribution = "©GDI-SL 2024"
    license = "cc-by-4.0"
    extensions = {"https://fiboa.org/flik-extension/v0.2.0/schema.yaml"}

    # The service publishes no area attribute, so it is derived from the geometry. The data is in
    # degrees, so post_migrate reprojects to an equal-area CRS and the result is already in m².
    area_is_in_ha = False
    area_calculate_missing = True

    columns = {
        "geometry": "geometry",
        "identifier": "id",
        "flik": "flik",  # derived in migrate(); NOT the id, one field block can hold several parcels
        "area": "metrics:area",  # not in the source; created by area_calculate_missing
        "name": "name",
    }
    missing_schemas = {"properties": {"name": {"type": "string"}}}

    def get_urls(self):
        # numberReturned is always reported as 0 by this server, so the page count has to come
        # from a hits request rather than from the responses themselves.
        hits = requests.get(BASE_URL, params={**PARAMS, "resultType": "hits"})
        hits.raise_for_status()
        total = int(re.search(r'numberMatched="(\d+)"', hits.text).group(1))

        query = urlencode({**PARAMS, "count": PAGE_SIZE})
        return {
            f"{BASE_URL}?{query}&startIndex={start}": f"de_sl_{start}.gml"
            for start in range(0, total, PAGE_SIZE)
        }

    def migrate(self, gdf):
        # The FLIK is the first 16 characters of the last underscore-separated segment of the
        # identifier, e.g. …_DESLLI00002529002224568 -> DESLLI0000252900. The remaining seven
        # digits number the application parcel within the field block.
        gdf["flik"] = gdf["identifier"].str.rsplit("_", n=1).str[-1].str[:16]
        return super().migrate(gdf)
