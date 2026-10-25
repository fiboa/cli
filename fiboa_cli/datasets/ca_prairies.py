import os
import re

import requests
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter

DATASET = "https://data.mendeley.com/public-api/datasets/2y568rt76w"
VERSION = 2
# The GeoParquet folders of version 2, one per province
FOLDERS = {
    "AB": "20824c18-4d05-4d21-90ef-e9996c034545",
    "SK": "edf6ac90-433b-4fdc-8e9e-791de025cf58",
    "MB": "ddc2076a-ca02-4487-87a7-3f0d2bd283ac",
}


class Converter(AdminConverterMixin, FiboaBaseConverter):
    id = "ca_prairies"
    short_name = "Canada, Prairies"
    title = "Field boundaries for the Canadian Prairies, derived from Sentinel-2"
    description = """
Field boundaries for Alberta, Saskatchewan and Manitoba, segmented from Sentinel-2 imagery of
2021-2024 with the Segment Anything Model by the University of Saskatchewan. The boundaries are
derived, not declared: no farmer or authority drew them. Seasonal RGB composites were segmented
without training data, the polygons cleaned and smoothed, and only those of at least 2 ha that
mostly lie on cropland (AAFC Annual Crop Inventory and ESA WorldCover) were kept. One file per
rural municipality (RM).
    """

    provider = "University of Saskatchewan <https://doi.org/10.17632/2y568rt76w.2>"
    attribution = (
        "Ha, T., Nketia, K., Neudorf, S., Shirtliffe, S. (2026): A field boundary dataset for the "
        "Canadian Prairies derived from Sentinel-2 imagery using the Segment Anything Model, "
        "Mendeley Data, V2, doi:10.17632/2y568rt76w.2"
    )
    license = "CC-BY-4.0"
    admin_country_code = "CA"

    columns = {
        "geometry": "geometry",
        "id": "id",
        "area_ha": "metrics:area",
        "border_len": "metrics:perimeter",
        "province": "admin:subdivision_code",
        "RM_number": "admin_local_code",
        "RM_name": "admin_local_name",
    }
    missing_schemas = {
        "properties": {
            "admin_local_code": {"type": "string"},
            "admin_local_name": {"type": "string"},
        }
    }

    def get_urls(self):
        """The download URLs of the GeoParquet files, named as Mendeley names them."""
        urls = {}
        for folder in FOLDERS.values():
            url = f"{DATASET}/files?folder_id={folder}&version={VERSION}"
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            for file in response.json():
                urls[file["content_details"]["download_url"]] = file["filename"]
        return urls

    def file_migration(self, gdf, path, uri, layer=None):
        # The province is only in the file name, e.g. Boundary_SK_ABERDEEN_373_intersect_cropland
        province = re.match(r"Boundary_([A-Z]{2})_", os.path.basename(path)).group(1)
        gdf["province"] = province
        # The GeoParquet files carry no field id; the row in the RM's file is stable
        gdf["id"] = [f"{province}-{rm}-{i}" for i, rm in enumerate(gdf["RM_number"])]
        return super().file_migration(gdf, path, uri, layer)
