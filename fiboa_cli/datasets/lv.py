import re
import unicodedata
from pathlib import Path

import pandas as pd
import requests
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin

# The resource URLs carry UUIDs, so the package is looked up by title.
CKAN = "https://data.gov.lv/dati/lv/api/3/action/package_search"
SEARCH = "Lauksaimnieku deklarētās platības"
# One GeoPackage per region, the same nine in every campaign; see _slug() for the spelling.
REGIONS = {
    "austrumlatgale",
    "dienvidkurzeme",
    "dienvidlatgale",
    "lielriga",
    "viduslatvija",
    "zemgale",
    "ziemelaustrumi",
    "ziemelkurzeme",
    "ziemelvidzeme",
}


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
        "crop:name": "crop:name",
        "period_code": "determination:datetime",
        "shape_area": "metrics:area",
        "shape_length": "metrics:perimeter",
    }
    missing_schemas = {
        "properties": {
            "block_id": {"type": "string"},
        }
    }
    # EuroCrops' lv_2021.csv plus the 34 codes the register added since
    ec_mapping_csv = "https://fiboa.org/code/lv/lv.csv"
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

        # "2024.gadā" and "2023. gadā" both occur; the search also matches descriptions,
        # so the title has to carry the phrase as well as the campaign
        wanted = re.compile(rf"\b{self.variant}\.\s*gad")
        matches = [
            p
            for p in packages
            if SEARCH.lower() in p.get("title", "").lower() and wanted.search(p["title"])
        ]
        if len(matches) != 1:
            titles = ", ".join(sorted(p.get("title", "") for p in matches)) or "none"
            raise ValueError(
                f"Expected one package for {self.variant} on data.gov.lv, found {len(matches)}: {titles}"
            )

        regions = {}
        for resource in matches[0]["resources"]:
            url = resource.get("url", "")
            if url.lower().endswith(".gpkg"):
                regions[_slug(resource.get("name") or Path(url).stem)] = url
        # a package that lost a region would otherwise be published as a partial edition
        if set(regions) != REGIONS:
            missing = ", ".join(sorted(REGIONS - set(regions))) or "none"
            unexpected = ", ".join(sorted(set(regions) - REGIONS)) or "none"
            raise RuntimeError(
                f"{matches[0]['title']} does not hold the nine regional GeoPackages "
                f"(missing: {missing}; unexpected: {unexpected})"
            )
        return {url: f"lv_{self.variant}_{region}.gpkg" for region, url in regions.items()}

    def post_migrate(self, gdf):
        gdf = super().post_migrate(gdf)
        # The files carry the code without a name; the code list has it.
        names = {row["original_code"].strip(): row["original_name"] for row in self.ec_mapping}
        gdf["crop:name"] = self.get_code_column(gdf).str.strip().map(names)
        return gdf

    def file_migration(self, gdf, path, uri, layer):
        # the campaigns up to 2023 name their columns in upper case
        gdf = gdf.rename(columns=str.lower)

        # objectid restarts at 1 in every regional file, so the region is part of the id:
        # 83,423 distinct objectids cover the 449,696 rows of the 2023 campaign
        region = _slug(layer or Path(path).stem)
        gdf["id"] = region + "-" + gdf["objectid"].astype("int64").astype(str)
        return gdf


def _slug(value: str) -> str:
    """A region name as ASCII, so the portal's "Lielrīga" (up to 2023) and "Lielriga" (2024
    onwards) give the same id."""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").lower()
    # the layer carries the campaign in some years, which the id already has
    return re.sub(r"_?(19|20)\d\d$", "", text)
