import re
from datetime import datetime

import requests

from fiboa_cli.datasets.es import ESBaseConverter


class EXConverter(ESBaseConverter):
    id = "es_ex"
    short_name = "Spain Extremadura"
    title = "Spain Extremadura Crop fields"
    description = """SIGPAC Crop fields of Spain - Extremadura"""
    license = "CC-BY-4.0"  # See http://sitex.gobex.es/SITEX/files/CondicionesUsoCICTEX.pdf
    attribution = "Junta de Extremadura"
    providers = [
        {
            "name": "Junta de Extremadura",
            "url": "https://www.juntaex.es/lajunta/consejeria-de-infraestructuras-transporte-y-vivienda",
            "roles": ["producer", "licensor"],
        }
    ]
    columns = {
        "geometry": "geometry",
        "id": "id",
        "provincia": "admin_province_code",
        "municipio": "admin_municipality_code",
        "uso_sigpac": "crop:code",
        "crop:name": "crop:name",
        "crop:name_en": "crop:name_en",
        "dn_surface": "area",
        "determination_datetime": "determination_datetime",
    }

    column_migrations = {
        "dn_surface": lambda x: x / 10000,
    }

    def migrate(self, gdf):
        gdf = super().migrate(gdf)
        gdf["determination_datetime"] = datetime(year=int(self.variant), month=1, day=1)
        return gdf

    missing_schemas = {
        "properties": {
            "admin_province_code": {"type": "string"},
            "admin_municipality_code": {"type": "string"},
        }
    }
    source_variants = {"2024": "TODO", "2023": "TODO"}

    def get_urls(self):
        if not self.variant:
            self.variant = next(iter(self.source_variants))

        from bs4 import BeautifulSoup

        base = "http://sitex.gobex.es/SITEX/centrodescargas/"
        soup = BeautifulSoup(requests.get(f"{base}viewsubcategoria/45").content, "html.parser")
        result = {}

        headers = {"X-Requested-With": "XMLHttpRequest", "X-Update": "resultadosdebusqueda"}
        values = [
            e.get("value")
            for e in soup.find("select", id="municipio").find_all("option")
            if e.get("value")
        ]
        for value in values:
            form = {
                "_method": "POST",
                "data[Datos][subcategoria_id]": 45,
                "data[Datos][nucleospoblacion_id]": value,
            }
            response = requests.post(f"{base}listadoresultados", data=form, headers=headers)
            soup = BeautifulSoup(response.content, "html.parser")
            matches = soup.find_all("a", href=re.compile(r"/SITEX/centrodescargas/descargar/"))
            m = matches[1 if self.variant == "2023" else 0].get("href")
            result[f"http://sitex.gobex.es/{m}"] = ["*.shp"]  # The single shapefile
        return result
