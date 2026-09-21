import re
from urllib.parse import urlencode

import requests
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter

# One service per campaign, each with the same three layers: the declared crops
# as a whole, and the arable and permanent-grassland subsets of them.
BASE_URL = "https://geoportal-w2.arimr.gov.pl/geoserver/gsa_public/uprawy_{year}/ows"
LAYER = "gsa_public:uprawy_rolne_{year}"
# 50,000 answers in about 90 seconds and 35 MB; the server caps neither.
PAGE_SIZE = 50_000


class Converter(AdminConverterMixin, FiboaBaseConverter):
    id = "pl"
    admin_country_code = "PL"
    short_name = "Poland"
    title = "Field boundaries for Poland"
    description = """
The agricultural parcels declared to ARiMR, the Polish paying agency, under the Geospatial
Application (GSA) of the Common Agricultural Policy. Every parcel carries the crop the farmer
declared on it, its plant group, and the support schemes it was declared under. The service
publishes the declarations of one campaign as a whole and, separately, its arable and
permanent-grassland parts; this is the whole.
"""

    provider = "Agencja Restrukturyzacji i Modernizacji Rolnictwa <https://www.gov.pl/web/arimr>"
    attribution = "© ARiMR"
    license = "CC-BY-4.0"

    extensions = {"https://fiboa.org/crop-extension/v0.2.0/schema.yaml"}

    variants = {year: year for year in ("2026", "2025")}
    use_variant_as_determination = True

    # The service states `pow` as hectares rounded to two decimals, which is the area of
    # the geometry to within 0.32% — EPSG:2180 is metric, so measuring it is exact and
    # needs no unit parsing.
    area_is_in_ha = False
    area_calculate_missing = True

    columns = {
        "geometry": "geometry",
        "id": "id",  # the record's own key, from the feature id
        "area": "metrics:area",  # not in the source; created by area_calculate_missing
        # The register classifies a parcel three times over, and numbers none of it:
        # 292 crop names fall under 155 short ones and those under 31 groups, each level
        # nesting cleanly in the next. The short name is the code a mapping would key on.
        "roslina_skrocona": "crop:code",
        "roslina": "crop:name",
        "grupa_roslin": "crop_group",
        "gr_upraw": "support_schemes",
    }

    missing_schemas = {
        "properties": {
            # "zboża" (cereals), "użytki zielone" (grassland), "sady plantacje trwałe"
            # (orchards and permanent plantations)
            "crop_group": {"type": "string"},
            # The schemes the parcel was declared under, comma-separated: ONW for a
            # less-favoured area, PWD for the basic payment, and so on.
            "support_schemes": {"type": "string"},
        }
    }

    def get_urls(self):
        if not self.variant:
            self.variant = next(iter(self.variants))
        base = BASE_URL.format(year=self.variant)

        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeNames": LAYER.format(year=self.variant),
            "outputFormat": "application/json",
        }
        hits = requests.get(base, params={**params, "resultType": "hits"}, timeout=180)
        hits.raise_for_status()
        total = int(re.search(r'numberMatched="(\d+)"', hits.text).group(1))
        self.info(f"{total:,} parcels in the {self.variant} campaign")

        query = urlencode({**params, "count": PAGE_SIZE})
        return {
            f"{base}?{query}&startIndex={start}": f"pl_{self.variant}_{start}.json"
            for start in range(0, total, PAGE_SIZE)
        }

    def file_migration(self, gdf, path, uri, layer=None):
        # read_geojson() hardcodes crs="EPSG:4326"; the service delivers EPSG:2180, and
        # its metres read as degrees reproject to nothing at all.
        return gdf.set_crs("EPSG:2180", allow_override=True)

    def migrate(self, gdf):
        # GeoServer answers with "uprawy_rolne_2026.160176865707"; the number is the
        # record's key in the register and identifies the parcel on its own.
        gdf["id"] = gdf["id"].str.rsplit(".", n=1).str[-1]
        return super().migrate(gdf)
