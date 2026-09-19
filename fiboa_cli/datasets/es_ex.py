from .commons.sigpac import SigpacRecintoMixin
from .es_base import ESBaseConverter


class EXConverter(SigpacRecintoMixin, ESBaseConverter):
    id = "es_ex"
    # Badajoz and Cáceres
    provinces = ("06", "10")
    short_name = "Spain Extremadura"
    title = "Spain Extremadura Crop fields"
    description = """SIGPAC recintos of Extremadura, from the national release by the Spanish
paying agency. The region's own download portal (sitex.gobex.es) has not answered since at
least 2026-09-10."""
    license = "CC-BY-4.0"
    attribution = "©FEGA / Ministerio de Agricultura, Pesca y Alimentación"
    provider = "Fondo Español de Garantía Agraria (FEGA) <https://www.fega.gob.es>"

    columns = {
        "geometry": "geometry",
        "id": "id",
        "provincia": "admin_province_code",
        "municipio": "admin_municipality_code",
        "uso_sigpac": "crop:code",
        "crop:name": "crop:name",
        "crop:name_en": "crop:name_en",
        "dn_surface": "metrics:area",
        "determination:datetime": "determination:datetime",  # the campaign, from the variant
    }
    missing_schemas = {
        "properties": {
            "admin_province_code": {"type": "string"},
            "admin_municipality_code": {"type": "string"},
        }
    }

    def get_urls(self):
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
