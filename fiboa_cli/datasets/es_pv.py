import pandas as pd
import requests

from .. import log
from .es import ESBaseConverter


class ESPVConverter(ESBaseConverter):
    source_variants = {
        str(
            year
        ): f"https://www.geo.euskadi.eus/cartografia/DatosDescarga/Agricultura/SIGPAC/SIGPAC_CAMPA%C3%91A_{year}_V1/"
        for year in range(2024, 2015, -1)
    }
    id = "es_pv"
    short_name = "Spain Basque Country"
    title = "Spain Basque Country Crop fields"
    description = """
    SIGPAC, the geographic information system for the identification of agricultural plots, is the system
    that farmers and ranchers must use to apply for community aid related to the area. The reason for
    putting this system into effect was the result of a requirement imposed by the European Union on
    all Member States. Sigpac began to be used from February 1, 2005, together with the beginning of
    the 2005 community aid application period.
    """
    providers = [
        {
            "name": "Basque Government",
            "url": "https://www.euskadi.eus/gobierno-vasco/inicio/",
            "roles": ["producer", "licensor"],
        }
    ]
    attribution = "Basque Government / Gobierno Vasco"
    license = "CC-BY-4.0"
    columns = {
        "geometry": "geometry",
        "id": "id",
        "CAMPANA": "determination_datetime",
        "USO": "crop:code",
        "crop:name": "crop:name",
    }

    column_migrations = {"CAMPANA": lambda col: pd.to_datetime(col, format="%Y")}
    use_code_attribute = "USO"
    index_as_id = True

    def get_urls(self):
        if not self.variant:
            self.variant = "2024"
            log(f"Choosing first variant {self.variant}", "warning")
        else:
            assert self.variant in self.source_variants

        from bs4 import BeautifulSoup

        # Parse list of zips in two steps from source url
        host = "https://www.geo.euskadi.eus"
        base = (
            f"/cartografia/DatosDescarga/Agricultura/SIGPAC/SIGPAC_CAMPA%C3%91A_{self.variant}_V1/"
        )
        soup = BeautifulSoup(requests.get(f"{host}/{base}").content, "html.parser")
        pages = [p["href"] for p in soup.find_all("a") if p["href"].startswith(base)]
        parsed = [
            BeautifulSoup(requests.get(f"{host}/{page}").content, "html.parser") for page in pages
        ]
        zips = [
            p["href"] for soup in parsed for p in soup.find_all("a") if p["href"].endswith(".zip")
        ]
        return {f"{host}{z}": z.rsplit("/", 1)[1] for z in zips}
