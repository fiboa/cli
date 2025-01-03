import re

import requests
from os import path, makedirs
import pandas as pd

from .es import ESBaseConverter
from ..util import log


# SOURCES = "https://filescartografia.navarra.es/2_CARTOGRAFIA_TEMATICA/2_6_SIGPAC/" # FULL Download timeout
class NCConverter(ESBaseConverter):
    id = "es_nc"
    short_name = "Spain Navarra"
    title = "Spain Navarra Crop fields"
    description = """
    SIGPAC Crop fields of Spain - Navarra
    """
    license = "CC-BY-4.0"  # https://sigpac.navarra.es/descargas/
    attribution = "Comunidad Foral de Navarra"
    providers = [
        {
            "name": "Comunidad Foral de Navarra",
            "url": "https://gobiernoabierto.navarra.es/",
            "roles": ["producer", "licensor"]
        }
    ]
    columns = {
        "id": "id",
        "geometry": "geometry",
        "BEGINLIFE": "determination_datetime",
        "IDUSO24": "crop:code",
        "crop:name": "crop:name",
        "crop:name_en": "crop:name_en",
    }
    column_migrations = {
        "BEGINLIFE": lambda col: pd.to_datetime(col, format="%d/%m/%Y"),
    }
    use_code_attribute = "IDUSO24"
    index_as_id = True

    def get_urls(self, cache=None):
        # scrape HTML page for sources
        content = requests.get("https://sigpac.navarra.es/descargas/", verify=False).text
        base = re.search('var rutaBase = "(.*?)";', content).group(1)
        last = base.rsplit('/', 1)[-1]
        sources = {f"https://sigpac.navarra.es/descargas/{base}{src}.zip": [f"{last}{src}.shp"] for src in
                   re.findall(r'value:"(\d+)"', content)}

        # Hostname has invalid SSL, hack around cache here
        if cache is None:
            log("Use -c <cache_dir> to prefill the cache dir, working around SSL errors", "warning")
            return sources

        makedirs(cache, exist_ok=True)
        log("Suppressing SSL-errors, filling cache with unverified SSL requests", "warning")
        requests.packages.urllib3.disable_warnings()  # Suppress InsecureRequestWarning
        for s in list(sources):
            target = path.join(cache, s.rsplit("/", 1)[1])
            if not path.exists(target):
                r = requests.get(s, verify=False)
                if r.status_code == 200:
                    with open(target, 'wb') as f:
                        f.write(r.content)
                else:
                    log(f"Skipping url {s}, status_code={r.status_code}", "error")
                    sources.pop(s)
        return sources
