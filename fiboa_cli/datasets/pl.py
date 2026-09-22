import re
from urllib.parse import urlencode

import requests
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin

# The workspace endpoint serves every layer; the per-layer endpoints of the large crop layers
# refuse connections. WFS 2.0 counts the whole layer on every request and times out, 1.1.0 does not.
WFS = "https://geoportal-w2.arimr.gov.pl/geoserver/gsa_public/wfs"
PAGE = 50_000  # the server's maximum
PARAMS = {
    "service": "WFS",
    "version": "1.1.0",
    "request": "GetFeature",
    "srsName": "EPSG:2180",
    "outputFormat": "SHAPE-ZIP",
    "format_options": "CHARSET:UTF-8",  # the default DBF charset loses the Polish letters
}


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    variants = {"2026": "uprawy_rolne_2026", "2025": "uprawy_rolne_2025"}
    id = "pl"
    short_name = "Poland"
    title = "Field boundaries for Poland"
    description = """
The agricultural parcels ("działki rolne") with the crops farmers declared to the paying agency
ARiMR in their geospatial aid applications, one campaign year per edition. The source names the
crop in Polish and has no crop code, so the name is the code as well. The area is the declared
area, the support schemes the parcel was declared under are listed as codes, and the id is the
position in the download, since the source carries no parcel identifier.
    """
    provider = "Agencja Restrukturyzacji i Modernizacji Rolnictwa <https://geoportal.arimr.gov.pl/mapy/apps/sites/#/portal>"
    attribution = "© ARiMR"
    # The portal tags the data "Publiczne dane ARIMR" but states no licence
    license = "Publiczne dane ARiMR, no licence stated <https://geoportal.arimr.gov.pl/mapy/apps/sites/#/portal>"
    ec_mapping_csv = "https://fiboa.org/code/pl/pl.csv"
    open_options = dict(encoding="UTF-8")  # GDAL does not read the .cst GeoServer writes
    use_variant_as_determination = True
    columns = {
        "geometry": "geometry",
        "id": "id",  # derived in file_migration()
        "roslina": "crop:name",
        "crop:code": "crop:code",  # the name, copied in migrate()
        "grupa_rosl": "crop_group",
        "gr_upraw": "support_schemes",
        "pow": "metrics:area",
        "determination:datetime": "determination:datetime",
    }
    column_migrations = {"pow": lambda col: col.str.removesuffix(" ha").astype(float)}
    missing_schemas = {
        "properties": {
            "crop_group": {"type": "string"},
            "support_schemes": {"type": "string"},
        }
    }

    def get_urls(self):
        layer = f"gsa_public:{self.variants[self.variant]}"
        # Any GeoJSON response carries the total; a hits request is capped at the page size
        first = requests.get(
            WFS,
            params={
                **PARAMS,
                "typeName": layer,
                "maxFeatures": 1,
                "propertyName": "pow",
                "outputFormat": "application/json",
            },
            timeout=120,
        )
        first.raise_for_status()
        total = first.json()["totalFeatures"]
        query = urlencode({**PARAMS, "typeName": layer, "maxFeatures": PAGE})
        return {
            f"{WFS}?{query}&startIndex={start}": f"pl_{self.variant}_{start:08d}.zip"
            for start in range(0, total, PAGE)
        }

    def file_migration(self, gdf, path, uri, layer=None):
        # The shapefile has no feature id; the pages are contiguous, so number the rows
        match = re.search(r"startIndex=(\d+)", uri)
        start = int(match.group(1)) if match else 0
        gdf["id"] = [f"{self.variant}-{start + i + 1}" for i in range(len(gdf))]
        return gdf

    def migrate(self, gdf):
        gdf["crop:code"] = gdf["roslina"]
        return super().migrate(gdf)
