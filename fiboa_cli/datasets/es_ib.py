import pandas as pd

from fiboa_cli.conversion.converter_rest import EsriRESTConverterMixin
from fiboa_cli.datasets.es_base import ESBaseConverter

CATALAN_MONTHS = (
    "gener febrer març abril maig juny juliol agost setembre octubre novembre desembre".split()
)


def snapshot_date(catxe):
    """'maig 2026' -> 2026-05-01"""
    try:
        month, year = str(catxe).strip().lower().split()
        return pd.Timestamp(year=int(year), month=CATALAN_MONTHS.index(month) + 1, day=1, tz="UTC")
    except (ValueError, AttributeError):
        return pd.NaT


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
        "determination:datetime": "determination:datetime",
    }
    column_additions = ESBaseConverter.column_additions | {"admin_province_code": "07"}
    area_is_in_ha = False
    missing_schemas = {
        "properties": {
            "admin_province_code": {"type": "string"},
            "admin_municipality_code": {"type": "string"},
        }
    }
    use_code_attribute = "USO_SIGPAC"

    # Since 2026 the service publishes a single layer with the current state
    # ("Recintes SIGPAC màxima actualitat"); the Catxe field names the month of
    # the snapshot, e.g. "maig 2026". The layer is a join, so the fields come
    # prefixed (SIGPAC_FOGAIBA.DN_OID, COD_Municipis.NOM, ...).
    rest_base_url = "https://ideib.caib.es/geoserveis/rest/services/public/GOIB_SIGPAC_IB/MapServer"
    rest_params = {
        "where": "USO_SIGPAC NOT IN ('AG','CA','ED','FO','IM','IS','IV','TH','ZC','ZU','ZV','MT')"
    }

    def rest_layer_filter(self, layers):
        return next(layer for layer in layers if "SIGPAC" in layer["name"].upper())

    def file_migration(self, gdf, path, uri, layer):
        gdf = gdf.rename(columns={c: c.rsplit(".", 1)[-1] for c in gdf.columns if "." in c})
        gdf["determination:datetime"] = gdf["Catxe"].map(snapshot_date)
        return gdf
