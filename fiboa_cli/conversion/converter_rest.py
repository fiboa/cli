import os
from urllib.parse import urlencode

import geopandas as gpd
import requests
from vecorel_cli.vecorel.util import get_fs, stream_file


class EsriRESTConverterMixin:
    cache_folder = None
    rest_base_url = None
    rest_params = {}
    rest_attribute = "OBJECTID"  # orderable, filterable, indexed
    rest_format = "geojson"  # servers before ArcGIS 10.4 only offer Esri JSON: "json"

    def rest_layer_filter(self, layers):
        return next(iter(layers))

    def get_urls(self):
        assert self.rest_base_url, (
            "Either define {c}.rest_base_url or override {c}.get_urls()".format(
                c=self.__class__.__name__
            )
        )
        return {"REST": self.rest_base_url}

    def download_files(self, uris, cache_folder=None):
        # Read-data will just stream all pages of rest-service
        if next(iter(uris), "").startswith("REST"):
            self.cache_folder = cache_folder
            return list(uris.values())

        # This happens when input_file param is used
        return super().download_files(uris, cache_folder)

    def get_data(self, paths, **kwargs):
        if not (isinstance(paths[0], str) and paths[0].startswith("http")):
            # This happens when the input_file param is used. Pages are read with the same
            # gpd.read_file() call as the REST branch below, deliberately rather than through
            # super().get_data(), for two reasons: Esri JSON carries a .json extension but is
            # not GeoJSON, and the base implementation's read_geojson() injects the GeoJSON
            # feature id as an "id" property, which collides with the "id" these converters
            # map from their own attribute. Reading a fixture must match a real run.
            for path, uri in paths:
                self.info(f"Reading {path} into GeoDataFrame")
                yield gpd.read_file(path), path, uri, None
            return

        base_url = paths[0]  # loop over paths to support more than 1 source
        source_fs = get_fs(base_url)
        cache_fs, cache_folder = self.get_cache(self.cache_folder)

        service_metadata = requests.get(base_url, {"f": "pjson"}).json()
        layer = self.rest_layer_filter(service_metadata["layers"])
        page_size = service_metadata["maxRecordCount"]
        layer_url = f"{base_url}/{layer['id']}/query"
        rest_params = dict(self.rest_params)
        base_where = rest_params.pop("where", None)  # combined with the paging filter below
        get_dict = rest_params | {
            "outFields": "*",
            "returnGeometry": "true",
            "f": self.rest_format,
            "sortBy": self.rest_attribute,
            "resultRecordCount": page_size,
        }
        gdfs = []
        last_id = -1
        while True:
            get_dict["where"] = f"{self.rest_attribute}>{last_id}"
            if base_where:
                get_dict["where"] += f" AND ({base_where})"
            url = f"{layer_url}?{urlencode(get_dict)}"
            if cache_fs is not None:
                cache_file = os.path.join(
                    cache_folder, f"{self.id}_{layer['id']}_{last_id}.{self.rest_format}"
                )
                if not cache_fs.exists(cache_file):
                    with cache_fs.open(cache_file, mode="wb") as file:
                        stream_file(source_fs, url, file)
                url = cache_file

            data = gpd.read_file(url)
            print(
                f"Read {len(data)} features, page {len(gdfs)} from [{data.iloc[0, 0]} ... {data.iloc[-1, 0]}]"
            )
            last_id = data[self.rest_attribute].values[-1]

            yield data, base_url, base_url, layer["id"]

            if not len(data) >= page_size:
                break
