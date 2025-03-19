import re
from datetime import datetime

import requests

from .es import ESBaseConverter


class ESVCConverter(ESBaseConverter):
    source_variants = {str(year): str(year) for year in range(2024, 2016 - 1, -1)}
    id = "es_vc"
    short_name = "Spain Valencia"
    title = "Spain Valencia Crop Fields"
    description = """
    Graphic layer of the plots and enclosures with defined agricultural uses that accompany the information of the
    Geographic Information System (SIGPAC) in the Valencian Community valid for the SIGPAC 2024 campaign
    (data dated 15-01-2024).
    """
    providers = [
        {
            "name": "Spanish Agricultural Guarantee Fund (FEGA) of the Ministry of Agriculture, Fisheries and Food",
            "url": "https://www.fega.gob.es/es/PwfGcp/es/el_fega/index.jsp",
            "roles": ["producer", "licensor"],
        }
    ]
    attribution = "© Institut Cartogràfic Valencià, Generalitat"
    license = "CC-BY-4.0"  # see http://www.icv.gva.es/condiciones-de-uso-de-la-geoinformacion-icv
    columns = {
        "DN_OID": "id",
        "geometry": "geometry",
        "PROVINCIA": "admin_province_code",
        "MUNICIPIO": "admin_municipality_code",
        "DN_SURFACE": "area",
        "USO_SIGPAC": "crop:code",
        "crop:name": "crop:name",
        "crop:name_en": "crop:name_en",
    }
    column_migrations = {
        "DN_SURFACE": lambda x: x / 10000,
    }
    missing_schemas = {
        "properties": {
            "admin_province_code": {"type": "string"},
            "admin_municipality_code": {"type": "string"},
        }
    }
    use_code_attribute = "USO_SIGPAC"

    def get_urls(self):
        if not self.variant:
            self.variant = next(iter(self.source_variants))
        self.column_additions["determination_datetime"] = datetime(int(self.variant), 1, 1)

        from bs4 import BeautifulSoup

        base = f"https://descargas.icv.gva.es/dcd/14_mediorural/03_pac/{self.variant}_SIGPAC_0050"
        soup = BeautifulSoup(requests.get(f"{base}").content, "html.parser")
        result = {
            f"{base}/{e.get('href')}": ["*/RECINTO.shp"]
            for e in soup.find_all("a", href=re.compile("1403_.*RECINTOS.*"))
        }
        return result
