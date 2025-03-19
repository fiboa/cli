from ..convert_utils import BaseConverter
from .commons.admin import AdminConverterMixin
from .commons.ec import EuroCropsConverterMixin, ec_url


class FRConverter(AdminConverterMixin, EuroCropsConverterMixin, BaseConverter):
    # TODO, 2022 works, check (or discover) paths for other years
    years = {
        2022: {
            "https://data.geopf.fr/telechargement/download/RPG/RPG_2-0__GPKG_LAMB93_FXX_2022-01-01/RPG_2-0__GPKG_LAMB93_FXX_2022-01-01.7z.001": [
                "RPG_2-0__GPKG_LAMB93_FXX_2022-01-01/RPG/1_DONNEES_LIVRAISON_2023-08-01/RPG_2-0_GPKG_LAMB93_FXX-2022/PARCELLES_GRAPHIQUES.gpkg"
            ]
        },
        2023: {
            "https://data.geopf.fr/telechargement/download/RPG/RPG_2-2__GPKG_LAMB93_FXX_2023-01-01/RPG_2-2__GPKG_LAMB93_FXX_2023-01-01.7z": [
                "RPG_2-2__GPKG_LAMB93_FXX_2023-01-01/RPG_2-2__GPKG_LAMB93_FXX_2023-01-01.gpkg"
            ]
        },
        2021: {
            "https://data.geopf.fr/telechargement/download/RPG/RPG_2-0__GPKG_LAMB93_FXX_2021-01-01/RPG_2-0__GPKG_LAMB93_FXX_2021-01-01.7z": [
                "RPG_2-0__GPKG_LAMB93_FXX_2022-01-01/RPG/1_DONNEES_LIVRAISON_2021-08-01/RPG_2-0_GPKG_LAMB93_FXX-2021/PARCELLES_GRAPHIQUES.gpkg"
            ]
        },
        2020: {
            "https://data.geopf.fr/telechargement/download/RPG/RPG_2-0__GPKG_LAMB93_FR_2020-01-01/RPG_2-0__GPKG_LAMB93_FR_2020-01-01.7z.001": [],
            "https://data.geopf.fr/telechargement/download/RPG/RPG_2-0__GPKG_LAMB93_FR_2020-01-01/RPG_2-0__GPKG_LAMB93_FR_2020-01-01.7z.002": [],
        },
        2019: {
            "https://data.geopf.fr/telechargement/download/RPG/RPG_2-0_GPKG_LAMB93_FR-2019/RPG_2-0_GPKG_LAMB93_FR-2019.7z": []
        },
        2018: {
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

    providers = [
        {
            "name": "Anstitut National de l'Information Géographique et Forestière",
            "url": "https://www.data.gouv.fr/en/datasets/registre-parcellaire-graphique-rpg-contours-des-parcelles-et-ilots-culturaux-et-leur-groupe-de-cultures-majoritaire/",
            "roles": ["producer", "licensor"],
        }
    ]
    # Attribution example as described in the open license
    attribution = "IGN — Original data from https://geoservices.ign.fr/rpg"
    license = {
        "title": "Licence Ouverte / Open Licence",
        "href": "https://etalab.gouv.fr/licence-ouverte-open-licence",
        "type": "text/html",
        "rel": "license",
    }
    ec_mapping_csv = "fr_2018.csv"
    extensions = {"https://fiboa.github.io/crop-extension/v0.1.0/schema.yaml"}
    column_additions = {"crop:code_list": ec_url(ec_mapping_csv)}

    columns = {
        "geometry": "geometry",
        "id_parcel": "id",
        "surf_parc": "area",
        "code_cultu": "crop:code",
        "code_group": "group_code",
    }

    column_filters = {
        "surf_parc": lambda col: col > 0.0  # fiboa validator requires area > 0.0
    }

    missing_schemas = {
        "properties": {
            "group_code": {"type": "string"},
        }
    }
