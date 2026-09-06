import re

from fiboa_cli.conversion.converter_rest import EsriRESTConverterMixin
from fiboa_cli.datasets.es_base import ESBaseConverter


class ESCBConverter(EsriRESTConverterMixin, ESBaseConverter):
    id = "es_cb"
    short_name = "Spain Cantabria"
    title = "Spain Cantabria Crop fields"
    description = "SIGPAC Crop fields of Spain - Cantabria"
    # Cantabria does not license its cartography under Creative Commons. Decreto
    # 87/2013 (modified by Decreto 102/2018) defines two licences of its own, both
    # free of charge: a non-commercial one and a commercial one, the latter needed
    # only for reselling the data. The Esri service names no licence at all, only
    # "Gobierno de Cantabria-FEGA" as copyright holder.
    # https://www.territoriodecantabria.es/cartografia-sig/descargas-y-politica-de-licencias/preguntas-frecuentes
    license = "Licencia de uso de datos del Gobierno de Cantabria (Decreto 87/2013) <https://www.territoriodecantabria.es/cartografia-sig/datos-abiertos-y-politica-de-licencias>"
    # The wording the licence requires for original data, verbatim.
    attribution = (
        "© Gobierno de Cantabria. Información gratuita disponible en https://mapas.cantabria.es"
    )
    provider = "Gobierno de Cantabria <https://mapas.cantabria.es>"
    columns = {
        "DN_OID": "id",
        "geometry": "geometry",
        "PROVINCIA": "admin_province_code",
        "MUNICIPIO": "admin_municipality_code",
        "DN_SURFACE": "metrics:area",
        "USO_SIGPAC": "crop:code",
        "crop:name": "crop:name",
        "crop:name_en": "crop:name_en",
    }
    area_is_in_ha = False
    missing_schemas = {
        "properties": {
            "admin_province_code": {"type": "string"},
            "admin_municipality_code": {"type": "string"},
        }
    }

    variants = {str(year): str(year) for year in range(2025, 2010 - 1, -1)}
    use_code_attribute = "USO_SIGPAC"
    use_variant_as_determination = True

    # "https://geoservicios.cantabria.es/inspire/rest/services/SIGPAC/MapServer?f=json"
    # "https://geoservicios.cantabria.es/inspire/rest/services/SIGPAC/MapServer/63/query?f=json&where=1%3D1&spatialRel=esriSpatialRelIntersects&geometry=%7B%22xmin%22%3A407913.2828037373%2C%22ymin%22%3A4804384.359524686%2C%22xmax%22%3A411054.4224193499%2C%22ymax%22%3A4805366.49482229%2C%22spatialReference%22%3A%7B%22wkid%22%3A25830%2C%22latestWkid%22%3A25830%7D%7D&geometryType=esriGeometryEnvelope&inSR=25830&outFields=OBJECTID%2CPROVINCIA%2CMUNICIPIO%2CAGREGADO%2CZONA%2CPOLIGONO%2CPARCELA%2CRECINTO%2CUSO_SIGPAC%2CSHAPE_Area&orderByFields=OBJECTID%20ASC&outSR=25830"

    rest_base_url = "https://geoservicios.cantabria.es/inspire/rest/services/SIGPAC/MapServer"
    # rest_params = {"where": "USO_SIGPAC NOT IN ('AG','CA','ED','FO','IM','IS','IV','TH','ZC','ZU','ZV','MT')"}

    def migrate(self, gdf):
        # 2010-2014 are joined layers: fields arrive table-qualified
        # (SIGPAC_2014_RECFE_ETRS89.PROVINCIA, SIGPAC_2014_ATRRE.USO_SIGPAC).
        # Strip the prefixes, first occurrence wins (the geometry table leads).
        if any("." in c for c in gdf.columns):
            renames = {}
            for c in gdf.columns:
                base = c.rsplit(".", 1)[-1]
                if base not in renames.values() and base not in gdf.columns:
                    renames[c] = base
            gdf = gdf.rename(columns=renames)
            gdf = gdf.loc[:, ~gdf.columns.duplicated()]
        return super().migrate(gdf)

    def rest_layer_filter(self, layers):
        if not self.variant:
            self.variant = next(iter(self.variants))
        regex = re.compile("Recintos SIGPAC " + self.variant)
        return next(layer for layer in layers if regex.match(layer["name"]))
