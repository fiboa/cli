import re
import unicodedata
from pathlib import Path

import pandas as pd
import requests
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin

# The yearly releases live on Latvia's open data portal, one package per campaign and
# nine regional GeoPackages in each. Their URLs carry dataset and resource UUIDs, so
# they cannot be constructed; the package is looked up by title instead. The slug is no
# help either: it reads "klientu-..." up to 2022 and "lauksaimnieku-..." after, and the
# 2015 package sits under a slug that says 2022.
CKAN = "https://data.gov.lv/dati/lv/api/3/action/package_search"
SEARCH = "Lauksaimnieku deklarētās platības"


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    id = "lv"
    short_name = "Latvia"
    title = "Latvia Lauki Parcels"
    description = """
Latvia offers parcel data on a [public map, available to any user](https://www.lad.gov.lv/lv/lauku-registra-dati).

The land register is a geographic information system (GIS) that gathers information about agricultural land eligible for state and European Union support from direct support scheme payments or environmental, climate, and rural landscape improvement payments.

The GIS of the field register contains a database of field blocks with interconnected spatial cartographic data and information of attributes subordinate to them: geographic attachment, identification numbers, and area information.

Each edition is the campaign the Rural Support Service published it for, taken from the
`period_code` the files carry themselves.
    """
    provider = "Rural Support Service Republic of Latvia (Lauku atbalsta dienests) <https://www.lad.gov.lv/lv/lauku-registra-dati>"
    attribution = "Lauku atbalsta dienests"
    license = "CC-BY-SA-4.0"  # Not sure, taken from Eurocrops. It is "public" and free and "available to any user"

    # The portal publishes 2015 onwards; every campaign has the same nine regions.
    variants = {str(year): str(year) for year in range(2025, 2014, -1)}

    columns = {
        "geometry": "geometry",
        "id": "id",
        "block_number": "block_id",
        "product_code": "crop:code",
        "period_code": "determination:datetime",
        "shape_area": "metrics:area",
        "shape_length": "metrics:perimeter",
    }
    missing_schemas = {
        "properties": {
            "block_id": {"type": "string"},
        }
    }
    ec_mapping_csv = "lv_2021.csv"
    column_migrations = {
        "product_code": lambda col: col.astype("string").str.strip(),
        "period_code": lambda col: pd.to_datetime(
            col.astype("string").str.strip() + "-01-01", format="%Y-%m-%d", utc=True
        ),
    }
    # The files are in LKS-92 / Latvia TM, so shape_area is already in square metres.
    area_is_in_ha = False
    area_calculate_missing = True

    def get_urls(self):
        response = requests.get(CKAN, params={"q": f'"{SEARCH}"', "rows": 100}, timeout=60)
        response.raise_for_status()
        packages = response.json()["result"]["results"]

        # "... 2024.gadā" and "... 2023. gadā" both occur
        wanted = re.compile(rf"\b{self.variant}\.\s*gad")
        matches = [p for p in packages if wanted.search(p.get("title", ""))]
        if len(matches) != 1:
            titles = ", ".join(sorted(p.get("title", "") for p in matches)) or "none"
            raise ValueError(
                f"Expected one package for {self.variant} on data.gov.lv, found {len(matches)}: {titles}"
            )

        urls = {}
        for resource in matches[0]["resources"]:
            url = resource.get("url", "")
            if not url.lower().endswith(".gpkg"):
                continue
            urls[url] = f"lv_{self.variant}_{_slug(resource.get('name') or Path(url).stem)}.gpkg"
        if len(urls) < 2:
            raise RuntimeError(f"{matches[0]['title']} holds {len(urls)} GeoPackage(s)")
        return urls

    def file_migration(self, gdf, path, uri, layer):
        # objectid is a row number that restarts at 1 in every regional file -- all 32,186
        # of Lielrīga's also occur in Zemgale -- so the region is part of the id. The layer
        # is named after the region, spelled differently from year to year, hence the slug.
        region = _slug(layer or Path(path).stem)
        gdf["id"] = region + "-" + gdf["objectid"].astype("int64").astype(str)
        return gdf


def _slug(value: str) -> str:
    """A region name as ASCII, so Lielrīga and lielrga give the same id."""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").lower()
