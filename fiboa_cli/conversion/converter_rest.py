import os
import re
import time
import zlib
from urllib.parse import urlencode

import geopandas as gpd
import requests
from vecorel_cli.vecorel.util import get_fs, stream_file

REST_ATTEMPTS = 8
REST_MAX_BACKOFF = 30  # seconds; eight attempts span about two minutes


class EsriRESTConverterMixin:
    cache_folder = None
    rest_base_url = None
    rest_params = {}
    rest_attribute = "OBJECTID"  # orderable, filterable, indexed
    rest_format = "geojson"  # servers before ArcGIS 10.4 only offer Esri JSON: "json"

    def rest_layer_filter(self, layers):
        return next(iter(layers))

    def get_urls(self):
        # An edition may live in a service of its own: es_ib keeps the current
        # snapshot in one and the yearly ones in another, so a variant whose
        # value is a URL names the service to read it from.
        url = self.variants.get(self.variant or next(iter(self.variants), ""))
        if not isinstance(url, str) or not url.startswith("http"):
            url = self.rest_base_url
        assert url, "Either define {c}.rest_base_url or override {c}.get_urls()".format(
            c=self.__class__.__name__
        )
        return {"REST": url}

    def download_files(self, uris, cache_folder=None):
        # Read-data will just stream all pages of rest-service
        if next(iter(uris), "").startswith("REST"):
            self.cache_folder = cache_folder
            return list(uris.values())

        # This happens when input_file param is used
        return super().download_files(uris, cache_folder)

    @staticmethod
    def _unqualify(gdf):
        """Drop the table prefix a joined layer puts on every field name.

        A join answers with SIGPAC_FOGAIBA.DN_OID rather than DN_OID, so a
        converter's `columns` match nothing. The first table wins, which is the
        one carrying the geometry.
        """
        if not any("." in c for c in gdf.columns):
            return gdf
        renames = {}
        for column in gdf.columns:
            name = column.rsplit(".", 1)[-1]
            if name not in gdf.columns and name not in renames.values():
                renames[column] = name
        gdf = gdf.rename(columns=renames)
        return gdf.loc[:, ~gdf.columns.duplicated()]

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
                yield self._unqualify(gpd.read_file(path)), path, uri, None
            return

        base_url = paths[0]  # loop over paths to support more than 1 source
        source_fs = get_fs(base_url)
        cache_fs, cache_folder = self.get_cache(self.cache_folder)

        service_metadata = self._rest_json(base_url, {"f": "pjson"})
        layer = self.rest_layer_filter(service_metadata["layers"])
        page_size = service_metadata["maxRecordCount"]
        layer_url = f"{base_url}/{layer['id']}/query"
        # Joined layers qualify every field with the table name, so read the key
        # field from the layer's metadata: es_ib refuses a "where=1=1" probe there.
        layer_metadata = self._rest_json(f"{base_url}/{layer['id']}", {"f": "pjson"})
        names = [field["name"] for field in layer_metadata.get("fields") or []]
        attribute = next(
            (n for n in names if n == self.rest_attribute),
            next((n for n in names if n.endswith("." + self.rest_attribute)), self.rest_attribute),
        )
        base_where = self.rest_params.get("where")

        # Page by half-open id windows rather than orderByFields + "id > last":
        # server-side sorting costs ~100 s per request on joined layers. The key
        # is unique, so a window of page_size ids cannot overflow a page.
        min_id = self._rest_id_bound(layer_url, attribute, base_where, "ASC")
        max_id = self._rest_id_bound(layer_url, attribute, base_where, "DESC")

        get_dict = self.rest_params | {
            "outFields": "*",
            "returnGeometry": "true",
            "f": self.rest_format,
        }
        # Layer ids repeat across services (every SIXPAC_<year> MapServer has its
        # Recintos layer at id 2), so the service must be part of the cache key.
        # So must the filter (de_st selects its edition by `where` alone, on one
        # service and one layer) and the window's upper bound: page_size follows
        # the service's maxRecordCount, and a page kept from a smaller one would
        # silently drop every id above its own bound.
        service = re.sub(r"\W+", "_", base_url.rstrip("/").split("/rest/services/")[-1])
        where_key = f"_w{zlib.crc32(base_where.encode()):08x}" if base_where else ""
        prefix = f"{self.id}_{service}_{layer['id']}{where_key}_r"
        windows = self._cached_windows(cache_fs, cache_folder, prefix)
        page = 0
        lo = min_id - 1
        while lo < max_id:
            cached = lo in windows
            hi = windows[lo] if cached else lo + page_size
            cache_file = None
            if cache_fs is not None:
                cache_file = os.path.join(cache_folder, f"{prefix}{lo}-{hi}.{self.rest_format}")
            if cached:
                try:
                    data = gpd.read_file(cache_file)
                except Exception as e:
                    cache_fs.rm(cache_file)
                    raise RuntimeError(f"Could not read cached page {cache_file}: {e}") from e
            else:
                clause = f"{attribute}>{lo} AND {attribute}<={hi}"
                get_dict["where"] = f"{clause} AND ({base_where})" if base_where else clause
                url = f"{layer_url}?{urlencode(get_dict)}"
                try:
                    data = self._rest_retry(
                        f"ids ({lo} ... {hi}]",
                        lambda: self._rest_page(source_fs, cache_fs, url, cache_file),
                    )
                except Exception as e:
                    raise RuntimeError(
                        f"Could not read ids ({lo} ... {hi}] of {layer_url}: {e}"
                    ) from e

            if len(data) == 0 and not cached:
                # An id gap wider than a page: ask once where the ids resume, and
                # let the empty page cover the whole gap on later runs, instead of
                # paging through a span that may hold millions of absent ids.
                resume = self._rest_id_bound(layer_url, attribute, base_where, "ASC", floor=lo)
                if resume - 1 > hi and cache_fs is not None:
                    gap = os.path.join(
                        cache_folder, f"{prefix}{lo}-{resume - 1}.{self.rest_format}"
                    )
                    cache_fs.mv(cache_file, gap)
                hi = max(hi, resume - 1)

            lo = hi
            if len(data) == 0:
                continue
            self.info(f"Read {len(data)} features, page {page} up to id {hi}")
            page += 1
            yield self._unqualify(data), base_url, base_url, layer["id"]

    @staticmethod
    def _cached_windows(cache_fs, cache_folder, prefix):
        """The cached (lo, hi] windows, keyed by lo. The name carries both bounds,
        so a page is only ever read as exactly the window it was fetched for."""
        if cache_fs is None or not cache_fs.exists(cache_folder):
            return {}
        pattern = re.compile(re.escape(prefix) + r"(-?\d+)-(-?\d+)\.")
        windows = {}
        for path in cache_fs.ls(cache_folder, detail=False):
            match = pattern.search(os.path.basename(str(path)))
            if match:
                windows[int(match.group(1))] = int(match.group(2))
        return windows

    def _rest_retry(self, what, action, attempts=REST_ATTEMPTS):
        """Run `action` until it succeeds: the Balearic proxy answers two requests
        in three with a 502, and a run makes hundreds of them."""
        for attempt in range(attempts):
            try:
                return action()
            except Exception as e:
                if attempt == attempts - 1:
                    raise
                self.warning(f"{what}: {e}, retrying ({attempt + 1}/{attempts})")
                time.sleep(min(2**attempt, REST_MAX_BACKOFF))

    def _rest_json(self, url, params):
        def ask():
            payload = requests.get(url, params).json()
            if "error" in payload:  # Esri answers a failed request with 200 and an error body
                raise RuntimeError(payload["error"])
            return payload

        return self._rest_retry(url, ask)

    @staticmethod
    def _rest_page(source_fs, cache_fs, url, cache_file):
        """Download and read one page; neither a download that broke off nor an
        error response survives as a cached page."""
        if cache_file is None:
            return gpd.read_file(url)
        try:
            with cache_fs.open(cache_file, mode="wb") as file:
                stream_file(source_fs, url, file)
            return gpd.read_file(cache_file)
        except Exception:
            if cache_fs.exists(cache_file):
                cache_fs.rm(cache_file)
            raise

    def _rest_id_bound(self, layer_url, attribute, base_where, direction, floor=-1):
        clause = f"{attribute}>{floor}"
        params = {
            "f": "json",
            "where": f"{clause} AND ({base_where})" if base_where else clause,
            "outFields": attribute,
            "returnGeometry": "false",
            "orderByFields": f"{attribute} {direction}",
            "resultRecordCount": 1,
        }
        response = self._rest_json(layer_url, params)
        return int(next(iter(response["features"][0]["attributes"].values())))
