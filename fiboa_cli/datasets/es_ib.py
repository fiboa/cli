import re

import pandas as pd

from fiboa_cli.conversion.converter_rest import EsriRESTConverterMixin
from fiboa_cli.datasets.es_base import ESBaseConverter

# The current snapshot lives in one service and the yearly ones in another.
CURRENT = "https://ideib.caib.es/geoserveis/rest/services/public/GOIB_SIGPAC_IB/MapServer"
HISTORIC = "https://ideib.caib.es/geoserveis/rest/services/public/GOIB_SIGPAC_HISTORIC_IB/MapServer"

CATALAN_MONTHS = (
    "gener febrer març abril maig juny juliol agost setembre octubre novembre desembre".split()
)


def snapshot_date(catxe):
    """The month the snapshot was taken: 'maig 2026' and 'Febrer2024.0' alike."""
    match = re.match(r"(\D+?)\s*(\d{4})", str(catxe).strip().lower())
    if not match or match.group(1) not in CATALAN_MONTHS:
        return pd.NaT
    month, year = match.groups()
    return pd.Timestamp(year=int(year), month=CATALAN_MONTHS.index(month) + 1, day=1, tz="UTC")


class ESIBConverter(EsriRESTConverterMixin, ESBaseConverter):
    id = "es_ib"
    short_name = "Spain Balearic Islands"
    title = "Spain Balearic Islands Crop fields"
    description = "SIGPAC Crop fields of Spain - Balearic Islands"
    # https://www.caib.es/sites/M170613081930629/f/463418
    # see https://intranet.caib.es/opendatacataleg/dataset/sigpac-2024/resource/3a0bc2e0-3f37-45b7-a7d4-1e8c7cf09bc8
    license = "CC-BY-4.0"  # http://www.opendefinition.org/licenses/cc-by
    attribution = "Govern de les Illes Balears"
    provider = "Govern de les Illes Balears <https://www.caib.es>"
    columns = {
        "DN_OID": "id",
        "geometry": "geometry",
        "MUNICIPIO": "admin_municipality_code",
        "DN_SURFACE": "metrics:area",
        "USO_SIGPAC": "crop:code",
        "crop:name": "crop:name",
        "crop:name_en": "crop:name_en",
        "Catxe": "determination:datetime",
    }
    column_migrations = {"Catxe": lambda col: pd.to_datetime(col.map(snapshot_date), utc=True)}
    column_additions = ESBaseConverter.column_additions | {"admin_province_code": "07"}
    area_is_in_ha = False
    missing_schemas = {
        "properties": {
            "admin_province_code": {"type": "string"},
            "admin_municipality_code": {"type": "string"},
        }
    }
    use_code_attribute = "USO_SIGPAC"

    # The current service holds one layer, "Recintes SIGPAC màxima actualitat",
    # which is ahead of the historic service's newest (maig against gener 2026).
    # The historic service starts at 2022; the layers before it are withdrawn.
    variants = {
        "2026": CURRENT,
        "2025": HISTORIC,
        "2024": HISTORIC,
        "2023": HISTORIC,
        "2022": HISTORIC,
    }
    rest_base_url = CURRENT
    # Both services join their parcels to the municipality and land-use tables,
    # so their fields arrive table-qualified; the REST mixin strips the prefixes.
    rest_params = {
        "where": "USO_SIGPAC NOT IN ('AG','CA','ED','FO','IM','IS','IV','TH','ZC','ZU','ZV','MT')"
    }

    def rest_layer_filter(self, layers):
        if not self.variant:
            self.variant = next(iter(self.variants))
        if self.variants[self.variant] == CURRENT:
            return next(layer for layer in layers if "SIGPAC" in layer["name"].upper())
        # "Recintes SIGPAC Illes Balears Febrer 2024", and a group layer above them
        return next(layer for layer in layers if layer["name"].strip().endswith(self.variant))
