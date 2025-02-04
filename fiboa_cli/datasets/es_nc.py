import re

import requests
from os import path, makedirs
import pandas as pd

from .es import ESBaseConverter
from ..util import log, name_from_uri


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

    def get_urls(self):
        # scrape HTML page for sources
        content = requests.get("https://sigpac.navarra.es/descargas/", verify=False).text
        base = re.search('var rutaBase = "(.*?)";', content).group(1)
        last = base.rsplit('/', 1)[-1]
        return {f"https://sigpac.navarra.es/descargas/{base}{src}.zip": [f"{last}{src}.shp"] for src in
                re.findall(r'value:"(\d+)"', content)}

    def prefill_cache(self, uris, cache_folder=None):
        if cache_folder is None:
            log("Use -c <cache_dir> to prefill the cache dir, working around SSL errors", "warning")
            return

        makedirs(cache_folder, exist_ok=True)
        log("Suppressing SSL-errors, filling cache with unverified SSL requests", "warning")
        requests.packages.urllib3.disable_warnings()  # Suppress InsecureRequestWarning
        for uri in list(uris):
            target = path.join(cache_folder, name_from_uri(uri))
            if not path.exists(target):
                r = requests.get(uri, verify=False)
                if r.status_code == 200:
                    with open(target, 'wb') as f:
                        f.write(r.content)
                else:
                    log(f"Skipping url {uri}, status_code={r.status_code}", "error")
                    uris.pop(uri)

    def download_files(self, uris, cache_folder=None):
        # Hostname has invalid SSL, prefill cache and avoid ssl-errors
        self.prefill_cache(uris, cache_folder)

        return super().download_files(uris, cache_folder=cache_folder)
