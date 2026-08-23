import json

import requests

from .es import ESBaseConverter

# IDEAragon lists every product of a collection that intersects a province
# (https://idearagon.aragon.es/descargas, collection "SIGPAC"). The per-province
# files (rec22/rec44/rec50_sigpac.shp.zip, ~1 GB RAR archives) are unreliable:
# the Teruel file disappeared from the server in 2026, so the much smaller
# per-municipality shapefiles are used instead.
PRODUCTS_URL = "https://idearagon.aragon.es/BD_GIS/getProductosColeccionIntersect.jsp"
DOWNLOAD_URL = (
    "https://icearagon.aragon.es/datosdescarga/descarga.php"
    "?file=/CartoTema/sigpac/{name}.shp.zip&blocksize=0"
)
PROVINCES = ("22", "44", "50")  # Huesca, Teruel, Zaragoza


class ARConverter(ESBaseConverter):
    # https://idearagon.aragon.es/descargas -> SIGPAC
    # The download list is fetched at runtime (see get_urls); the files are
    # overwritten in place every campaign, the product list carries the year.
    id = "es_ar"
    short_name = "Spain Aragon"
    title = "Spain Aragon Crop fields"
    description = """
SIGPAC - Sistema de Información Geográfica de la Política Agrícola común (ejercicio actual)

Crop Fields of Spain province Aragon
    """
    provider = "Gobierno de Aragon <https://www.aragon.es>"

    # License: https://idearagon.aragon.es/portal/politica-privacidad.jsp
    license = "CC-BY-4.0"
    attribution = "(c) Gobierno de Aragon"
    columns = {
        "geometry": "geometry",
        "DN_OID": "id",
        "PROVINCIA": "admin_province_code",
        "MUNICIPIO": "admin_municipality_code",
        "SUPERFICIE": "metrics:area",
        "USO_SIGPAC": "crop:code",
        "crop:name": "crop:name",
        "crop:name_en": "crop:name_en",
        "determination:datetime": "determination:datetime",
    }
    area_is_in_ha = False
    use_code_attribute = "USO_SIGPAC"

    column_migrations = {
        "DN_OID": lambda col: col.astype("int64"),
    }

    missing_schemas = {
        "properties": {
            "admin_province_code": {"type": "string"},
            "admin_municipality_code": {"type": "string"},
        }
    }

    # Campaign year of the downloaded files, taken from the product list.
    # Falls back to the --variant when the files are given explicitly.
    edition_year = None

    @staticmethod
    def list_products(province):
        response = requests.post(
            PRODUCTS_URL,
            data={
                "idesquema": f"{province}provincia",
                "coleccion": "SIGPAC",
                "esquema": "provincia",
            },
            timeout=120,
        )
        response.raise_for_status()
        # the service emits a trailing comma before the closing bracket
        text = response.text.replace("\n", "").replace("},]}", "}]}").strip()
        return json.loads(text)["productos"]

    def get_urls(self):
        urls = {}
        years = set()
        for province in PROVINCES:
            for product in self.list_products(province):
                name = product["name"]
                # the intersection also returns neighbouring municipalities
                if product["esquema"] != "Municipio" or not name.startswith(province):
                    continue
                urls[DOWNLOAD_URL.format(name=name)] = f"es_ar_{name}.shp.zip"
                years.add(str(product["fecha"])[:4])
        if not urls:
            raise ValueError("No SIGPAC municipality files listed by IDEAragon")
        self.edition_year = max(years)
        self.info(f"{len(urls)} municipality files, campaign {self.edition_year}")
        return urls

    def post_migrate(self, gdf):
        gdf = super().post_migrate(gdf)
        year = self.edition_year or self.variant
        if year:
            gdf["determination:datetime"] = f"{year}-01-01T00:00:00Z"
        else:
            self.warning("Unknown campaign year, determination:datetime is not set")
        return gdf
