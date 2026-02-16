from geopandas import GeoDataFrame
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import AddHCATMixin


class FRConverter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    # TODO, 2022 works, check (or discover) paths for other years
    variants = {
        "2022": {
            "https://data.geopf.fr/telechargement/download/RPG/RPG_2-0__GPKG_LAMB93_FXX_2022-01-01/RPG_2-0__GPKG_LAMB93_FXX_2022-01-01.7z.001": [
                "**/*.gpkg"
            ]
        },
        "2023": {
            "https://data.geopf.fr/telechargement/download/RPG/RPG_2-2__GPKG_LAMB93_FXX_2023-01-01/RPG_2-2__GPKG_LAMB93_FXX_2023-01-01.7z": [
                "**/*.gpkg"
            ]
        },
        "2021": {
            "https://data.geopf.fr/telechargement/download/RPG/RPG_2-0__GPKG_LAMB93_FXX_2021-01-01/RPG_2-0__GPKG_LAMB93_FXX_2021-01-01.7z": [
                "**/*.gpkg"
            ]
        },
        "2020": {
            "https://data.geopf.fr/telechargement/download/RPG/RPG_2-0__GPKG_LAMB93_FR_2020-01-01/RPG_2-0__GPKG_LAMB93_FR_2020-01-01.7z.001": [],
            "https://data.geopf.fr/telechargement/download/RPG/RPG_2-0__GPKG_LAMB93_FR_2020-01-01/RPG_2-0__GPKG_LAMB93_FR_2020-01-01.7z.002": [],
        },
        "2019": {
            "https://data.geopf.fr/telechargement/download/RPG/RPG_2-0_GPKG_LAMB93_FR-2019/RPG_2-0_GPKG_LAMB93_FR-2019.7z": []
        },
        "2018": {
            "https://data.geopf.fr/telechargement/download/RPG/RPG_2-0__SHP_LAMB93_FR-2017_2017-01-01/RPG_2-0__SHP_LAMB93_FR-2017_2017-01-01.7z": []
        },
    }
    id = "fr"
    short_name = "France"
    title = "Registre Parcellaire Graphique; Crop Fields France"
    description = """
France has published Crop Field data for many years. Crop fields are declared by farmers within the Common Agricultural Policy (CAP) subsidy scheme.

The anonymized version is distributed as part of the public service for making reference data available contains graphic data for plots (basic land unit for farmers' declaration) with their main crop. This data has been produced by the Services and Payment Agency (ASP) since 2007.
    """

    provider = "Anstitut National de l'Information Géographique et Forestière <https://www.data.gouv.fr/en/datasets/registre-parcellaire-graphique-rpg-contours-des-parcelles-et-ilots-culturaux-et-leur-groupe-de-cultures-majoritaire/>"
    # Attribution example as described in the open license
    attribution = "IGN - Original data from https://geoservices.ign.fr/rpg"
    license = "Licence Ouverte / Open Licence <https://etalab.gouv.fr/licence-ouverte-open-licence>"
    ec_mapping_csv = "fr_2018.csv"

    columns = {
        "geometry": "geometry",
        "id_parcel": "id",
        "surf_parc": "metrics:area",
        "code_cultu": "crop:code",
        "code_group": "group_code",
    }

    def migrate(self, gdf) -> GeoDataFrame:
        if "ID_PARCEL" in gdf.columns:
            # Make column names lowercase, harmonize for different years
            gdf.rename(columns={k: k.lower() for k in gdf.columns}, inplace=True)
        return super().migrate(gdf)

    column_filters = {
        "surf_parc": lambda col: col > 0.0  # fiboa validator requires area > 0.0
    }

    missing_schemas = {
        "properties": {
            "group_code": {"type": "string"},
        }
    }
