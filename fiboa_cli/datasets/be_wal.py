import geopandas as gpd
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.convert_gml import gml_assure_columns
from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import ec_url


class Converter(AdminConverterMixin, FiboaBaseConverter):
    sources = {
        "https://geoservices.wallonie.be/geotraitement/spwdatadownload/get/2a0d9be0-ac3d-443e-9db0-a7cfb0f128e2/LU_ExistingLandUse_SIGEC2022.gml.zip?blocksize=0": [
            "LU_ExistingLandUse_SIGEC2022.gml"
        ]
    }
    id = "be_wal"
    admin_region_code = "WAL"
    short_name = "Belgium, Wallonia"
    title = "Belgium Wallonia: Parcellaire Agricole Anonyme"
    description = """
    The Crop Fields (PAA) covers land use in agricultural and forestry areas managed as part of the implementation of the
    Common Agricultural Policy by the Paying Agency of Wallonia.

    The PAA represents the public version of the agricultural plot. It therefore does not include personal information
    allowing the operator to be identified. It is provided on an annual basis. Data from a year of cultivation are made
    available to the public during the following year.

    The data is distributed in two ways: either at the source of the paying agency (more attributes
    but no public distribution) or at the European Commission data portal (no limitations). We use the
    free-licensed version for this converter.
    """
    providers = [
        {
            "name": "Inspire Geoportal of the European Commission",
            "url": "https://inspire-geoportal.ec.europa.eu/srv/eng/catalog.search#/metadata/2a0d9be0-ac3d-443e-9db0-a7cfb0f128e2",
            "roles": ["host", "processor"],
        }
    ]
    license = {
        "title": "No conditions apply to access and use. Distributed through Inspire guidelines",
        "href": "https://inspire-geoportal.ec.europa.eu/srv/eng/catalog.search#/metadata/2a0d9be0-ac3d-443e-9db0-a7cfb0f128e2",
        "type": "text/html",
        "rel": "license",
    }
    columns = {
        "geometry": "geometry",
        "crop_name": "crop:name",
        "crop_code": "crop:code",
        "id": "id",
        "determination:datetime": "determination:datetime",
    }
    column_additions = {
        "determination:datetime": "2022-01-01T00:00:00Z",
        "crop:code_list": ec_url("be_wal_all_years.csv"),
    }
    column_migrations = {
        "crop_code": lambda col: col.str.extract(r"\.(\d+)$", expand=False),
        "crop_name": lambda col: col.str.strip(),
    }
    extensions = {"https://fiboa.github.io/crop-extension/v0.2.0/schema.yaml"}

    index_as_id = True

    def layer_filter(self, layer: str, uri: str) -> bool:
        return layer == "ExistingLandUseObject"

    def file_migration(
        self, gdf: gpd.GeoDataFrame, path: str, uri: str, layer: str = None
    ) -> gpd.GeoDataFrame:
        return gml_assure_columns(
            gdf,
            path,
            uri,
            layer,
            crop_name={"ElementPath": "specificLandUse@title", "Type": "String", "Width": 255},
            crop_code={"ElementPath": "specificLandUse@href", "Type": "String", "Width": 255},
        )
