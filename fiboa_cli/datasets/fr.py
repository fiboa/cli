from geopandas import GeoDataFrame
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import AddHCATMixin


class FRConverter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    # TODO, 2022 works, check (or discover) paths for other years
    variants = {
        "2024": {
            "https://data.geopf.fr/telechargement/download/RPG/RPG_3-0__GPKG_LAMB93_FXX_2024-01-01/RPG_3-0__GPKG_LAMB93_FXX_2024-01-01.7z.001": [
                "**/RPG_Parcelles.gpkg"  # RPG 3.0 renamed PARCELLES_GRAPHIQUES.gpkg
            ],
            "https://data.geopf.fr/telechargement/download/RPG/RPG_3-0__GPKG_LAMB93_FXX_2024-01-01/RPG_3-0__GPKG_LAMB93_FXX_2024-01-01.7z.002": [],
            "https://data.geopf.fr/telechargement/download/RPG/RPG_3-0__GPKG_LAMB93_FXX_2024-01-01/RPG_3-0__GPKG_LAMB93_FXX_2024-01-01.7z.003": [],
            "https://data.geopf.fr/telechargement/download/RPG/RPG_3-0__GPKG_LAMB93_FXX_2024-01-01/RPG_3-0__GPKG_LAMB93_FXX_2024-01-01.7z.004": [],
            "https://data.geopf.fr/telechargement/download/RPG/RPG_3-0__GPKG_LAMB93_FXX_2024-01-01/RPG_3-0__GPKG_LAMB93_FXX_2024-01-01.7z.005": [],
        },
        "2023": {
            "https://data.geopf.fr/telechargement/download/RPG/RPG_2-2__GPKG_LAMB93_FXX_2023-01-01/RPG_2-2__GPKG_LAMB93_FXX_2023-01-01.7z": [
                "**/PARCELLES_GRAPHIQUES.gpkg"
            ]
        },
        "2022": {
            "https://data.geopf.fr/telechargement/download/RPG/RPG_2-0__GPKG_LAMB93_FXX_2022-01-01/RPG_2-0__GPKG_LAMB93_FXX_2022-01-01.7z.001": [
                "**/PARCELLES_GRAPHIQUES.gpkg"
            ]
        },
        "2021": {
            "https://data.geopf.fr/telechargement/download/RPG/RPG_2-0__GPKG_LAMB93_FXX_2021-01-01/RPG_2-0__GPKG_LAMB93_FXX_2021-01-01.7z": [
                "**/PARCELLES_GRAPHIQUES.gpkg"
            ]
        },
        "2020": {
            "https://data.geopf.fr/telechargement/download/RPG/RPG_2-0__GPKG_LAMB93_FR_2020-01-01/RPG_2-0__GPKG_LAMB93_FR_2020-01-01.7z.001": [
                "**/PARCELLES_GRAPHIQUES.gpkg"
            ],
            "https://data.geopf.fr/telechargement/download/RPG/RPG_2-0__GPKG_LAMB93_FR_2020-01-01/RPG_2-0__GPKG_LAMB93_FR_2020-01-01.7z.002": [],
        },
        "2019": {
            "https://data.geopf.fr/telechargement/download/RPG/RPG_2-0_GPKG_LAMB93_FR-2019/RPG_2-0_GPKG_LAMB93_FR-2019.7z": [
                "**/PARCELLES_GRAPHIQUES.gpkg"
            ]
        },
        # the newest SHP edition on the download server is 2017; there is no 2018 archive
        "2017": {
            "https://data.geopf.fr/telechargement/download/RPG/RPG_2-0__SHP_LAMB93_FR-2017_2017-01-01/RPG_2-0__SHP_LAMB93_FR-2017_2017-01-01.7z": [
                "**/PARCELLES_GRAPHIQUES.shp"
            ]
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
    # One merged list for all editions: EuroCrops splits France over two tables
    # and misses eleven newer codes (e.g. JAC, the most common code of 2024)
    hcat_mapping_csv = "https://fiboa.org/code/fr/fr.csv"

    columns = {
        "geometry": "geometry",
        "id": "id",
        "parcel_id": "parcel_id",
        "surf_parc": "metrics:area",
        "code_cultu": "crop:code",
        "code_group": "group_code",
    }

    def migrate(self, gdf) -> GeoDataFrame:
        if "ID_PARCEL" in gdf.columns:
            # Make column names lowercase, harmonize for different years
            gdf = gdf.rename(columns={k: k.lower() for k in gdf.columns})

        # the source reissues some parcel ids; the base converter numbers the repeats
        gdf["parcel_id"] = gdf["id_parcel"]
        gdf["id"] = gdf["id_parcel"].astype("string")
        return super().migrate(gdf)

    column_filters = {
        "surf_parc": lambda col: col > 0.0  # fiboa validator requires area > 0.0
    }

    missing_schemas = {
        "properties": {
            "group_code": {"type": "string"},
            "parcel_id": {"type": "string"},
        }
    }
