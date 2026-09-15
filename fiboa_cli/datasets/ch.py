import pandas as pd
import requests
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin

SERVICES_URL = "https://www.geodienste.ch/info/services.json?base_topics=lwb_nutzungsflaechen"
# The other publication states are "Registrierung erforderlich" (NE, TI), "Freigabe
# erforderlich" (NW, OW, VD) and "keine Daten / Bereitstellung" (FL); their downloads answer 401.
OPEN = "Frei erhältlich"


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
    # The catalogue is published by the BLW as LWB_Nutzungsflaechen_Kataloge.xlsx; this is its
    # LNF_Katalog_Nutzungsart sheet as CSV.
    column_additions = {"crop:code_list": "https://fiboa.org/code/ch/lnf_code.csv"}
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
        # geodienste.ch lists every canton with its publication state, INTERLIS model version and
        # STAC item. The GeoPackage link embeds the model version (v2_0 / v3_0), which changes when
        # a canton migrates, so the links are looked up at run time instead of being hard-coded.
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
        # nutzungsidentifikator is the "Identifikator" of the LWB_Nutzungsflaechen model, the
        # canton's own id of the plot. Its format differs per canton (AG 4001112N014,
        # ZG ZG.KUL.19570, ZH 131581) and values repeat across cantons, so the canton code is
        # prefixed to make it unique nationally.
        gdf["id"] = gdf["kanton"] + "-" + gdf["nutzungsidentifikator"]
        return super().migrate(gdf)
