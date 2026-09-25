import pandas as pd
import requests
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin

SERVICES_URL = "https://www.geodienste.ch/info/services.json?base_topics=lwb_nutzungsflaechen"
SERVICE_PAGE = "https://www.geodienste.ch/services/lwb_nutzungsflaechen"
OPEN = "Frei erhältlich"  # the others need registration or the canton's approval
# the federal usage catalogue with its HCAT mapping; the cantons share the codes, not the names
CODE_LIST = "https://fiboa.org/code/ch/lnf_code.csv"

# Terms as the Info column of the geodienste.ch service page shows them (2026-09-24): CC-BY-4.0
# where the source is required, CC0-1.0 for "Freie Nutzung", the canton's own conditions where no
# opendata.swiss term is shown. source: the citation the canton prescribes, or its name.
# access: the canton publishes on request only. BS is left out: its file is empty, its plots are
# in the BL file.
CANTONS = {
    "AG": {"name": "Aargau", "license": "CC-BY-4.0", "source": "Daten des Kantons Aargau"},
    "AI": {
        "name": "Appenzell Innerrhoden",
        "license": "CC-BY-4.0",
        "source": "Grundlage/Quelle: Geodaten Kanton/Bezirke Appenzell I.Rh.",
    },
    "AR": {
        "name": "Appenzell Ausserrhoden",
        "license": "CC0-1.0",
        "source": "Kanton Appenzell Ausserrhoden",
    },
    "BE": {"name": "Bern", "license": "CC-BY-4.0", "source": "Kanton Bern, Amt für Geoinformation"},
    "BL": {"name": "Basel-Landschaft", "license": "CC-BY-4.0", "source": "Kanton Basel-Landschaft"},
    "FR": {
        "name": "Fribourg",
        "license": "CC-BY-4.0",
        "source": "État de Fribourg / Kanton Freiburg",
    },
    "GE": {"name": "Geneva", "license": "CC-BY-4.0", "source": "Données SITG, État de Genève"},
    "GL": {"name": "Glarus", "license": "CC0-1.0", "source": "Kanton Glarus"},
    "GR": {
        "name": "Graubünden",
        "license": "Nutzungsbestimmungen für Geodaten <https://geo.gr.ch/geodaten/nutzungsbedingungen>",
        # the canton's own syntax: "Quelle: [Datenbestand], Kanton Graubünden"
        "attribution": f"Quelle: Landwirtschaftliche Nutzungsflächen, Kanton Graubünden, {SERVICE_PAGE}",
    },
    "JU": {
        "name": "Jura",
        "license": "CC-BY-4.0",
        "source": "Géodonnées de la République et Canton du Jura",
    },
    "LU": {"name": "Luzern", "license": "CC-BY-4.0", "source": "Kanton Luzern"},
    "NE": {
        "name": "Neuchâtel",
        "license": "CC-BY-4.0",
        "source": "Données SITN, http://www.ne.ch/sitn",
        "access": "registration",
    },
    "NW": {
        "name": "Nidwalden",
        "license": "GIS Daten AG Nutzungsbestimmungen für Geodaten und Geodienste <https://www.gis-daten.ch/downloads/public/Richtlinien_Weisungen/Nutzungsbestimmungen_Geodaten_und_Geodienste.pdf>",
        "source": "Quelle: GIS Daten AG, Kanton Nidwalden",
        "access": "approval",
    },
    "OW": {
        "name": "Obwalden",
        "license": "GIS Daten AG Nutzungsbestimmungen für Geodaten und Geodienste <https://www.gis-daten.ch/downloads/public/Richtlinien_Weisungen/Nutzungsbestimmungen_Geodaten_und_Geodienste.pdf>",
        "source": "Quelle: GIS Daten AG, Kanton Obwalden",
        "access": "approval",
    },
    "SG": {
        "name": "St. Gallen",
        "license": "Nutzungsbedingungen für Geodaten <https://www.sg.ch/bauen/geoinformation/datenbezug/agb.html>",
        "source": "Kanton St.Gallen",
    },
    "SH": {"name": "Schaffhausen", "license": "CC0-1.0", "source": "Kanton Schaffhausen"},
    "SO": {"name": "Solothurn", "license": "CC0-1.0", "source": "Kanton Solothurn"},
    "SZ": {
        "name": "Schwyz",
        "license": "CC-BY-4.0",
        "source": "Amt für Landwirtschaft (AFL), Kanton Schwyz",
    },
    "TG": {"name": "Thurgau", "license": "CC-BY-4.0", "source": "Kanton Thurgau"},
    "TI": {
        "name": "Ticino",
        "license": "CC-BY-4.0",
        "source": "Fonte: Amministrazione cantonale - Canton Ticino",
        "access": "registration",
    },
    "UR": {"name": "Uri", "license": "CC-BY-4.0", "source": "Quelle: Lisag AG (GIS Uri)"},
    "VD": {
        "name": "Vaud",
        "license": "Conditions d'utilisation des géodonnées <https://www.vd.ch/territoire-et-construction/cadastre-et-geoinformation/geodonnees/commande-de-geodonnees/conditions-dutilisation/>",
        "source": "État de Vaud",
        "access": "approval",
    },
    "VS": {"name": "Valais", "license": "CC-BY-4.0", "source": "Canton du Valais / Kanton Wallis"},
    "ZG": {"name": "Zug", "license": "CC-BY-4.0", "source": "Quelle: GIS Kanton Zug"},
    "ZH": {
        "name": "Zürich",
        "license": "CC0-1.0",
        "source": "Kanton Zürich, Amt für Landschaft und Natur",
    },
}
ACCESS = {
    "registration": "Registration on geodienste.ch is required for this canton",
    "approval": "The canton has to approve the download on geodienste.ch",
}


class CHBaseConverter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    """One canton of the Swiss usage areas ("Nutzungsflächen", federal model 153.1).

    Reads the canton's GeoPackage from geodienste.ch and fills the metadata from CANTONS, so a
    subclass only names its canton. A canton with its own archive declares `variants` (None is
    the geodienste.ch file, anything else its own source) and `source_columns`.
    """

    canton = ""  # two letters, set by the subclass
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
        "lnf_code": lambda col: col.notna(),  # crop:code is required
    }
    area_is_in_ha = False
    area_calculate_missing = True
    column_migrations = {
        "bezugsjahr": lambda col: pd.to_datetime(col.astype(int), format="%Y"),
        # crop:code is a string
        "lnf_code": lambda col: col.astype(str),
        "flaeche_m2": lambda col: col.astype(float),
    }
    hcat_mapping_csv = CODE_LIST
    # Combine canton with internal id to make it unique
    id_columns = ("kanton", "nutzungsidentifikator")

    # a canton's own archive: its column names mapped to the model's, and its area unit in m²
    source_columns = {}
    area_factor = 1

    def __init__(self, *args, **kwargs):
        if self.canton:
            info = CANTONS[self.canton]
            self.id = self.id or f"ch_{self.canton.lower()}"
            self.short_name = self.short_name or f"Switzerland, {info['name']}"
            self.title = (
                self.title or f"Field boundaries for the canton of {info['name']}, Switzerland"
            )
            self.description = self.description or (
                f"The agricultural usage areas (Nutzungsflächen) of the canton of {info['name']}, "
                "in their current state on geodienste.ch."
            )
            self.provider = (
                self.provider or f"Kanton {info['name']}, via geodienste.ch <{SERVICE_PAGE}>"
            )
            self.license = self.license or info["license"]
            self.attribution = self.attribution or info.get(
                "attribution",
                f"{info.get('source')} — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}",
            )
            if info.get("access") and not self.data_access:
                self.data_access = (
                    f"{ACCESS[info['access']]}: apply at {SERVICE_PAGE}, export the GeoPackage "
                    f"and convert it with `fiboa convert {self.id} -i <zip>|geopackage/*.gpkg`."
                )
        super().__init__(*args, **kwargs)
        assert not self.canton or self.id == f"ch_{self.canton.lower()}", "id must be ch_<canton>"

    def select_variant(self, variant):
        super().select_variant(variant)
        if self.variants and self.variant not in self.variants:
            raise ValueError(
                f"Unknown variant '{self.variant}', choose from {', '.join(self.variants)}"
            )

    def get_services(self):
        services = requests.get(SERVICES_URL, timeout=60)
        services.raise_for_status()
        return sorted(services.json()["services"], key=lambda s: s["canton"])

    @staticmethod
    def get_geopackage_url(service):
        # the link embeds the model version (v2_0/v3_0)
        item = requests.get(service["stac_item_url"], timeout=60)
        item.raise_for_status()
        return item.json()["assets"]["geopackage_zip"]["href"]

    def get_urls(self):
        if self.variants and self.variants[self.variant] is not None:
            return self.variants[self.variant]  # the canton's own source for that year
        service = next((s for s in self.get_services() if s["canton"] == self.canton), None)
        if service is None:
            raise ValueError(f"{self.canton} is not listed on geodienste.ch")
        if service["publication_data"] != OPEN:
            raise ValueError(f"{self.canton}: {service['publication_data']}. {self.data_access}")
        return {self.get_geopackage_url(service): ["geopackage/*.gpkg"]}

    def file_migration(self, gdf, path, uri, layer=None):
        if "nutzungsidentifikator" in gdf.columns:
            # a geodienste.ch file is the canton's current publication: it must be the variant's year
            if self.variants and (gdf["bezugsjahr"] != int(self.variant)).any():
                years = ", ".join(str(y) for y in sorted(gdf["bezugsjahr"].unique()))
                raise ValueError(
                    f"{self.canton}: the geodienste.ch file holds {years}, not {self.variant}; "
                    "add the year as a variant"
                )
            return gdf
        # the canton's own layer; "0613" and 613.0 both become 613, the string cast follows the filters
        gdf = gdf.rename(columns=self.source_columns)
        gdf["lnf_code"] = pd.to_numeric(gdf["lnf_code"]).astype("Int64")
        if "flaeche_m2" in gdf.columns and self.area_factor != 1:
            gdf["flaeche_m2"] = gdf["flaeche_m2"] * self.area_factor
        if "bezugsjahr" in gdf.columns:
            gdf["bezugsjahr"] = pd.to_numeric(gdf["bezugsjahr"]).astype("Int64")
        else:
            gdf["bezugsjahr"] = int(self.variant)
        gdf["kanton"] = self.canton
        gdf["ist_ueberlagernd"] = False  # the cantons' own layers have no overlapping elements
        return gdf
