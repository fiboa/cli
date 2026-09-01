import os
import re
from urllib.parse import urlencode

import geopandas as gpd
import requests
from vecorel_cli.vecorel.util import get_fs, stream_file


class EsriRESTConverterMixin:
    cache_folder = None
    rest_base_url = None
    rest_params = {}
    rest_attribute = "OBJECTID"  # orderable, filterable, indexed

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
        # Read-data will just stream alle pages of rest-service
        if next(iter(uris), "").startswith("REST"):
            self.cache_folder = cache_folder
            return list(uris.values())

        # This happens when input_file param is used
        return super().download_files(uris, cache_folder)

    def get_data(self, paths, **kwargs):
        if isinstance(paths[0], tuple):
            # (path, uri) pairs from the base downloader: input_file param was used
            yield from super().get_data(paths, **kwargs)
            return

        base_url = paths[0]  # loop over paths to support more than 1 source
        source_fs = get_fs(base_url)
        cache_fs, cache_folder = self.get_cache(self.cache_folder)

        service_metadata = requests.get(base_url, {"f": "pjson"}).json()
        layer = self.rest_layer_filter(service_metadata["layers"])
        page_size = service_metadata["maxRecordCount"]
        layer_url = f"{base_url}/{layer['id']}/query"
        # Joined layers qualify every field with the table name; discover the
        # real key field before paging on it ("OBJECTID" alone fails there).
        probe = requests.get(
            layer_url,
            {
                "f": "json",
                "where": "1=1",
                "outFields": "*",
                "resultRecordCount": 1,
                "returnGeometry": "false",
            },
        ).json()
        attribute = self.rest_attribute
        if probe.get("features"):
            names = list(probe["features"][0]["attributes"].keys())
            attribute = next(
                (n for n in names if n == self.rest_attribute),
                next(
                    (n for n in names if n.endswith("." + self.rest_attribute)), self.rest_attribute
                ),
            )
        base_where = self.rest_params.get("where")

        # Page by half-open id windows instead of orderByFields + "id > last":
        # server-side sorting costs ~100 s per request on joined layers, while a
        # range filter on the indexed key answers in about a second. The key is
        # unique, so a window of page_size ids cannot overflow a page; id gaps
        # only produce empty windows, which are skipped.
        min_id = self._rest_id_bound(layer_url, attribute, base_where, "ASC")
        max_id = self._rest_id_bound(layer_url, attribute, base_where, "DESC")

        get_dict = self.rest_params | {
            "outFields": "*",
            "returnGeometry": "true",
            "f": "geojson",
        }
        # Layer ids repeat across services (every SIXPAC_<year> MapServer has its
        # Recintos layer at id 2), so the service must be part of the cache key.
        service = re.sub(r"\W+", "_", base_url.rstrip("/").split("/rest/services/")[-1])
        page = 0
        lo = min_id - 1
        while lo < max_id:
            hi = lo + page_size
            data = None
            if cache_fs is not None:
                data = self._window_from_legacy_cache(
                    cache_fs, cache_folder, layer["id"], lo, hi, page_size
                )
            if data is None:
                clause = f"{attribute}>{lo} AND {attribute}<={hi}"
                get_dict["where"] = f"({base_where}) AND {clause}" if base_where else clause
                url = f"{layer_url}?{urlencode(get_dict)}"
                if cache_fs is not None:
                    cache_file = os.path.join(
                        cache_folder, f"{self.id}_{service}_{layer['id']}_r{lo}.geojson"
                    )
                    if not cache_fs.exists(cache_file):
                        try:
                            with cache_fs.open(cache_file, mode="wb") as file:
                                stream_file(source_fs, url, file)
                        except Exception:
                            # A download that broke off must not survive as a cached page
                            if cache_fs.exists(cache_file):
                                cache_fs.rm(cache_file)
                            raise
                    url = cache_file

                try:
                    data = gpd.read_file(url)
                except Exception as e:
                    # An error response from the server must not survive as a cached page
                    if cache_fs is not None and cache_fs.exists(url):
                        cache_fs.rm(url)
                    raise RuntimeError(
                        f"Could not read ids ({lo} ... {hi}] of {layer_url}: {e}"
                    ) from e

            lo = hi
            if len(data) == 0:
                continue
            print(f"Read {len(data)} features, page {page} from ids ({hi - page_size} ... {hi}]")
            page += 1
            yield data, base_url, base_url, layer["id"]

    def _rest_id_bound(self, layer_url, attribute, base_where, direction):
        clause = f"{attribute}>-1"
        response = requests.get(
            layer_url,
            {
                "f": "json",
                "where": f"({base_where}) AND {clause}" if base_where else clause,
                "outFields": attribute,
                "returnGeometry": "false",
                "orderByFields": f"{attribute} {direction}",
                "resultRecordCount": 1,
            },
        ).json()
        return int(next(iter(response["features"][0]["attributes"].values())))

    def _window_from_legacy_cache(self, cache_fs, cache_folder, layer_id, lo, hi, page_size):
        """Pages cached by the old sorted paging are keyed by the previous page's
        last id. On dense layers they coincide exactly with an id window, so reuse
        one when its ids prove it covers (lo, hi] completely."""
        for key in [-1, lo] if lo == 0 else [lo]:
            path = os.path.join(cache_folder, f"{self.id}_{layer_id}_{key}.geojson")
            if not cache_fs.exists(path):
                continue
            try:
                data = gpd.read_file(path)
            except Exception:
                continue
            id_column = next(
                (
                    c
                    for c in data.columns
                    if c == self.rest_attribute or c.endswith("." + self.rest_attribute)
                ),
                None,
            )
            if id_column is None or len(data) == 0:
                continue
            ids = data[id_column]
            covers = (len(data) == page_size and ids.max() == hi) or (
                len(data) < page_size and ids.max() <= hi
            )
            if ids.min() == lo + 1 and covers:
                return data
        return None
