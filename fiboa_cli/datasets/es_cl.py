import re
import os
import requests

from .es import ESBaseConverter
from .. import log

regex = re.compile(r"\d+_(RECFE|BURGOS).*\.shp$")


class ESCLConverter(ESBaseConverter):
    id = "es_cl"
    short_name = "Spain Castilla y León"
    title = "Spain Castile and León Crop fields"
    description = """
    Official SIGPAC land plan for the year 2024. (reference date 02-01-2024)

    Source: SIGPAC (FEGA) database. The Land Consolidation Replacement Farms are included,
    not updated in the SIGPAC published in the Viewer.
    Data manager: Ministry of Agriculture, Fisheries and Food.
    Data provided by: Department of Agriculture, Livestock and Rural Development. Regional Government of Castile and Leon.
    Free use of the data is permitted, but commercial exploitation is prohibited.
    """
    providers = [
        {
            "name": "Department of Agriculture, Livestock and Rural Development. Regional Government of Castile and Leon",
            "url": "https://www.itacyl.es/",
            "roles": ["producer", "licensor"]
        }
    ]
    license = {
        "title": "CC-NC: Free use of the data is permitted, but commercial exploitation is prohibited",
        "href": "http://ftp.itacyl.es/cartografia/LICENCIA-IGCYL-NC-2012.pdf" ,
        "type": "application/pdf",
        "rel": "license"
    }

    columns = {
        "DN_OID": "id",
        "geometry": "geometry",
        "determination_datetime": "determination_datetime",
        "USO_SIGPAC": "crop:code",
        "crop:name": "crop:name",
        "crop:name_en": "crop:name_en",
    }
    use_code_attribute = "USO_SIGPAC"
    column_additions = ESBaseConverter.column_additions | {
        "determination_datetime": "2024-01-01T00:00:00Z"
    }

    def download_files(self, uris, cache_folder=None):
        paths = super().download_files(uris, cache_folder)
        new = []
        for path, uri in paths:
            directory = os.path.dirname(path)
            ps = [z for z in os.listdir(directory) if regex.search(z)]
            assert len(ps), f"Missing matching shapefile in {directory}"
            for p in ps:
                new.append((os.path.join(directory, p), uri))
        return new

    def get_urls(self):
        if not self.variant:
            self.variant = "2024"
            log(f"Choosing first variant {self.variant}", "warning")
        else:
            assert self.variant in "2024 2023 2022 2021 2020 2019".split(), f"Wrong variant {self.variant}"
        base = f"http://ftp.itacyl.es/cartografia/05_SIGPAC/{self.variant}_ETRS89/Parcelario_SIGPAC_CyL_Provincias/"
        response = requests.get(base)
        assert response.status_code == 200, f"Error getting urls {response}\n{response.content}"
        uris = {f"{base}{g}": ["replaceme.zip"] for g in re.findall(r'href="(\w+.zip)"', response.text)}
        return uris
