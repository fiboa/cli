import os
import shutil
import tempfile
import zipfile

import geopandas as gpd
import pandas as pd
import pyogrio
import requests
from vecorel_cli.conversion.duckdb import DuckDBBaseConverter

from ..conversion.fiboa_converter import FiboaBaseConverter

API = "https://restapi.fude.maff.go.jp"
BASE = "https://opendata.fude.maff.go.jp"
# MAFF's CDN refuses requests that do not look like a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
}
PREFECTURES = [f"{code:02d}" for code in range(1, 48)]


class JPConverter(DuckDBBaseConverter, FiboaBaseConverter):
    # One zip of municipality GeoJSONs per prefecture; the URLs only work signed, see download_files
    variants = {
        str(year): {
            f"{BASE}/{year}/{year}_{pref}.zip": f"jp_fude_{year}_{pref}.zip" for pref in PREFECTURES
        }
        for year in range(2026, 2020, -1)
    }

    id = "jp"
    short_name = "Japan"
    title = "Japan Fude Parcels"
    description = """
Japanese Farmland Parcel Polygons (Fude Polygons in Japanese) represent parcel information of farmland.
The polygons are manually digitized data derived from aerial imagery, such as satellite images. Since no
on-site verification or similar procedures have been conducted, the data may not necessarily match the actual
current conditions. Fude Polygons are created for the purpose of roughly indicating the locations of farmland.
    """

    provider = "Japanese Ministry of Agriculture, Forestry and Fisheries (MAFF, 農林水産省) <https://download.fude.maff.go.jp/>"
    attribution = "出典：「筆ポリゴンデータ」（農林水産省）を加工して作成"
    license = "CC-BY-4.0"

    columns = {
        "geometry": "geometry",
        "polygon_uuid": "id",
        "land_type": "land_type_en",
        "local_government_cd": "admin_local_code",
        "issue_year": "determination:datetime",
    }
    # SQL migrations (DuckDB converter): per-feature determination date from the issue year
    column_migrations = {
        "land_type": "CASE land_type WHEN 100 THEN 'rice_field' WHEN 200 THEN 'field' END",
        "issue_year": "make_timestamp(CAST(issue_year AS INTEGER), 1, 1, 0, 0, 0) AT TIME ZONE 'UTC'",
    }
    missing_schemas = {
        "properties": {
            "land_type_en": {"type": "string"},
            "admin_local_code": {"type": "string"},
        }
    }

    def select_variant(self, variant):
        super().select_variant(variant)
        # MAFF's terms ask for this wording, naming the edition and that it was processed
        self.attribution = (
            f"出典：「筆ポリゴンデータ（{self.variant}年度公開）」（農林水産省）を加工して作成"
        )

    def convert(self, output_file, cache=None, **kwargs):
        self._parquet_dir = tempfile.mkdtemp(prefix="jp_fude_")
        try:
            # the zips must go through download_files, which DuckDBBaseConverter skips without a cache
            cache = cache or self._parquet_dir
            return super().convert(output_file, cache=cache, **kwargs)
        finally:
            shutil.rmtree(self._parquet_dir, ignore_errors=True)

    def download_files(self, uris, cache_folder=None, **kwargs):
        cache_fs, cache_folder = self.get_cache(cache_folder)
        missing = [
            uri
            for uri, name in uris.items()
            if "://" in uri and not cache_fs.exists(os.path.join(cache_folder, name))
        ]
        signed = self.sign(missing)
        uris = {signed.get(uri, uri): name for uri, name in uris.items()}
        kwargs["client_kwargs"] = {"headers": HEADERS}
        zips = super().download_files(uris, cache_folder, **kwargs)
        return [self.to_parquet(path[0] if isinstance(path, tuple) else path) for path in zips]

    def sign(self, uris):
        """The download URLs of the API, signed for 30 minutes, for the given unsigned URLs."""
        if not uris:
            return {}
        prefectures = [uri.rsplit("_", 1)[1].removesuffix(".zip") for uri in uris]
        body = {
            "issue_year": self.variant,
            "pref_cd": prefectures,
            "pref_name": self.prefecture_names(prefectures),
            "city_cd": [],
            "city_name": [],
        }
        response = requests.post(
            f"{API}/download/lambda-download", json=body, headers=HEADERS, timeout=60
        )
        response.raise_for_status()
        signed = {found["url"].split("?")[0]: found["url"] for found in response.json()["found"]}
        return {uri: signed[uri] for uri in uris}

    def prefecture_names(self, codes):
        url = f"{API}/getprefcitycd/lambda-getprefcitycd?issue_year={self.variant}"
        response = requests.get(url, headers=HEADERS, timeout=60)
        response.raise_for_status()
        names = {p["pref_cd"]: p["pref_name"] for p in response.json()[0]}
        return [names[code] for code in codes]

    def to_parquet(self, zip_path):
        """One GeoParquet file of all municipality GeoJSONs in a prefecture zip."""
        target = os.path.join(
            self._parquet_dir, os.path.basename(zip_path).replace(".zip", ".parquet")
        )
        with zipfile.ZipFile(zip_path) as archive:
            members = sorted(n for n in archive.namelist() if n.endswith(".json"))
        frames = [pyogrio.read_dataframe(f"/vsizip/{zip_path}/{member}") for member in members]
        gdf = gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs=frames[0].crs)
        # each geometry declares JGD2011, which GDAL ignores
        gdf = gdf.set_crs(6668, allow_override=True)
        gdf.drop(columns=["history"]).to_parquet(target)
        return target
