import pandas as pd
import requests
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin

SERVICES_URL = "https://www.geodienste.ch/info/services.json?base_topics=lwb_nutzungsflaechen"
SERVICE_PAGE = "https://www.geodienste.ch/services/lwb_nutzungsflaechen"
OPEN = "Frei erhältlich"  # the other states are "Registrierung erforderlich" and "Freigabe erforderlich"
# The federal usage catalogue (LNF_Katalog_Nutzungsart) with its HCAT mapping; every canton codes
# its usages with it, the names differ in language and abbreviation.
CODE_LIST = "https://fiboa.org/code/ch/lnf_code.csv"


class CHBaseConverter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    """
    One canton of the Swiss agricultural usage areas ("Nutzungsflächen", federal model 153.1).

    The cantons publish their data through geodienste.ch under their own terms; this base reads
    the canton's GeoPackage from there. A canton with an archive of its own overrides `variants`
    and `get_urls` and renames its columns to the model's names in `file_migration`.
    """

    canton = ""  # two letters, set by the subclass
    provider = (
        "Konferenz der kantonalen Geoinformations- und Katasterstellen <https://www.kgk-cgc.ch>"
    )
    columns = {
        "geometry": "geometry",
        "flaeche_m2": "metrics:area",
        "kanton": "admin:subdivision_code",
        "lnf_code": "crop:code",
        "nutzung": "crop:name",
        "bezugsjahr": "determination:datetime",
    }
    column_filters = {
        "ist_ueberlagernd": lambda col: col == False,  # noqa: E712
    }
    area_is_in_ha = False
    area_calculate_missing = True
    column_migrations = {
        "bezugsjahr": lambda col: pd.to_datetime(col.astype(int), format="%Y"),
        # crop:code must be a string per the crop extension; lnf_code is an integer.
        "lnf_code": lambda col: col.astype(str),
        "flaeche_m2": lambda col: col.astype(float),
    }
    ec_mapping_csv = CODE_LIST
    # Combine canton with internal id to make it unique
    id_columns = ("kanton", "nutzungsidentifikator")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert not self.canton or self.id == f"ch_{self.canton.lower()}", "id must be ch_<canton>"

    def get_services(self):
        services = requests.get(SERVICES_URL, timeout=60)
        services.raise_for_status()
        return sorted(services.json()["services"], key=lambda s: s["canton"])

    @staticmethod
    def get_geopackage_url(service):
        # the link embeds the model version (v2_0/v3_0), so it is looked up rather than hardcoded
        item = requests.get(service["stac_item_url"], timeout=60)
        item.raise_for_status()
        return item.json()["assets"]["geopackage_zip"]["href"]

    def get_urls(self):
        # A year whose variant entry is None comes from geodienste.ch; any other entry is the
        # canton's own source for that year.
        if self.variants and self.variants.get(self.variant) is not None:
            return self.variants[self.variant]
        service = next(s for s in self.get_services() if s["canton"] == self.canton)
        if service["publication_data"] != OPEN:
            raise ValueError(f"{self.canton}: {service['publication_data']}. {self.data_access}")
        return {self.get_geopackage_url(service): ["geopackage/*.gpkg"]}
