import pandas as pd
import requests
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin

SERVICES_URL = "https://www.geodienste.ch/info/services.json?base_topics=lwb_nutzungsflaechen"
OPEN = "Frei erhältlich"  # NE, TI need registration; NW, OW, VD approval; FL has no data


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    id = "ch"
    short_name = "Switzerland"
    title = "Field boundaries for Switzerland"
    description = "The cropfields of Switzerland (Nutzungsflächen) are published per administrative subdivision called Canton."
    provider = (
        "Konferenz der kantonalen Geoinformations- und Katasterstellen <https://www.kgk-cgc.ch>"
    )
    license = "opendata.swiss terms of use <https://opendata.swiss/en/terms-of-use>"
    columns = {
        "geometry": "geometry",
        "id": "id",  # derived in migrate()
        "flaeche_m2": "metrics:area",
        "kanton": "admin:subdivision_code",
        "lnf_code": "crop:code",  # code of the federal usage catalogue (LNF_Katalog_Nutzungsart)
        "nutzung": "crop:name",
        "bezugsjahr": "determination:datetime",
    }
    column_filters = {
        "ist_ueberlagernd": lambda col: col == False,  # noqa: E712
    }
    area_is_in_ha = False
    area_calculate_missing = True
    column_migrations = {
        "bezugsjahr": lambda col: pd.to_datetime(col, format="%Y"),
        # crop:code must be a string per the crop extension; lnf_code is an integer.
        "lnf_code": lambda col: col.astype(str),
    }
    ec_mapping_csv = "https://fiboa.org/code/ch/ch.csv"

    def get_urls(self):
        # Look up each open canton's GeoPackage; the link embeds the model version (v2_0/v3_0).
        services = requests.get(SERVICES_URL, timeout=60)
        services.raise_for_status()

        urls = {}
        for service in sorted(services.json()["services"], key=lambda s: s["canton"]):
            if service["publication_data"] != OPEN:
                self.info(f"Skipping canton {service['canton']}: {service['publication_data']}")
                continue
            item = requests.get(service["stac_item_url"], timeout=60)
            item.raise_for_status()
            urls[item.json()["assets"]["geopackage_zip"]["href"]] = ["geopackage/*.gpkg"]
        return urls

    def migrate(self, gdf):
        # Combine canton with internal id to make it unique
        gdf["id"] = gdf["kanton"] + "-" + gdf["nutzungsidentifikator"]
        return super().migrate(gdf)
