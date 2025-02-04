from urllib.parse import urlencode

import requests


class EsriRESTPregenerateConverterMixin:
    # Mixin class for BaseConveter
    # Requires self.rest_base_url, pointing to an ESRI Rest Mapservice
    # Overrides self.get_urls() to discover available layers. Generates a list of paged source-urls
    rest_base_url = None
    rest_params = {"where": "OBJECTID>=0"}

    def rest_layer_filter(self, layers):
        return next(iter(layers))

    def get_urls(self):
        service_metadata = requests.get(f"{self.rest_base_url}/", {"f": "pjson"}).json()
        layer = self.rest_layer_filter(service_metadata["layers"])
        page_size = service_metadata["maxRecordCount"]

        layer_url = f"{self.rest_base_url}/{layer['id']}/query"
        count_params = self.rest_params | {"returnCountOnly": "true", "f": "pjson"}
        layer_count = requests.get(layer_url, count_params).json()["count"]
        nr_pages = (layer_count + page_size - 1) // page_size

        get_dict = self.rest_params | {"outFields": "*", "returnGeometry": "true", "f": "geojson"}
        return {
            f"{layer_url}?{urlencode(get_dict | dict(resultRecordCount=page_size, resultOffset=page_size * page))}":
                f"{self.id}_{self.variant or ''}_{page}.json"
            for page in range(nr_pages)
        }

