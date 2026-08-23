import os
import re

import multivolumefile
import py7zr
from geopandas import GeoDataFrame
from vecorel_cli.conversion.admin import AdminConverterMixin
from vecorel_cli.vecorel.util import name_from_uri

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
        "2024": {
            "https://data.geopf.fr/telechargement/download/RPG/RPG_3-0__GPKG_LAMB93_FXX_2024-01-01/RPG_3-0__GPKG_LAMB93_FXX_2024-01-01.7z.001": [],
            "https://data.geopf.fr/telechargement/download/RPG/RPG_3-0__GPKG_LAMB93_FXX_2024-01-01/RPG_3-0__GPKG_LAMB93_FXX_2024-01-01.7z.002": [],
            "https://data.geopf.fr/telechargement/download/RPG/RPG_3-0__GPKG_LAMB93_FXX_2024-01-01/RPG_3-0__GPKG_LAMB93_FXX_2024-01-01.7z.003": [],
            "https://data.geopf.fr/telechargement/download/RPG/RPG_3-0__GPKG_LAMB93_FXX_2024-01-01/RPG_3-0__GPKG_LAMB93_FXX_2024-01-01.7z.004": [],
            "https://data.geopf.fr/telechargement/download/RPG/RPG_3-0__GPKG_LAMB93_FXX_2024-01-01/RPG_3-0__GPKG_LAMB93_FXX_2024-01-01.7z.005": [],
        },
        "2023": {
            "https://data.geopf.fr/telechargement/download/RPG/RPG_2-2__GPKG_LAMB93_FXX_2023-01-01/RPG_2-2__GPKG_LAMB93_FXX_2023-01-01.7z": [
                "**/*.gpkg"
            ]
        },
        "2021": {
            "https://data.geopf.fr/telechargement/download/RPG/RPG_2-0__GPKG_LAMB93_FXX_2021-01-01/RPG_2-0__GPKG_LAMB93_FXX_2021-01-01.7z": [
                "**/PARCELLES_GRAPHIQUES.gpkg"
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

    def download_files(self, uris, cache_folder=None):
        """Multi-volume 7z archives (.7z.001, .7z.002, ...) are one 7z stream split
        into parts; py7zr reads them through multivolumefile, vecorel-cli does not."""
        volumes = [uri for uri in uris if re.search(r"\.7z\.\d{3}$", uri)]
        if not volumes:
            return super().download_files(uris, cache_folder)
        others = {uri: target for uri, target in uris.items() if uri not in volumes}
        # download the parts as plain files (no extraction by the base class)
        parts = super().download_files({uri: name_from_uri(uri) for uri in volumes}, cache_folder)
        name = name_from_uri(volumes[0])  # <name>.7z.001
        archive = parts[0][0][: -len(".001")]
        _, cache_dir = self.get_cache(cache_folder)
        folder = os.path.join(cache_dir, "extracted." + os.path.splitext(name)[0])
        if not os.path.exists(folder):
            self.info(f"Extracting {len(parts)} volumes of {os.path.basename(archive)}")
            with multivolumefile.MultiVolume(archive, mode="rb", ext_digits=3) as volume:
                with py7zr.SevenZipFile(volume, "r") as sz:
                    sz.extractall(folder)
        targets = next(
            (uris[uri] for uri in volumes if uris[uri]), ["**/PARCELLES_GRAPHIQUES.gpkg"]
        )
        paths = [(os.path.join(folder, target), volumes[0]) for target in targets]
        if others:
            paths.extend(super().download_files(others, cache_folder))
        return paths

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
            gdf = gdf.rename(columns={k: k.lower() for k in gdf.columns}, inplace=True)
        return super().migrate(gdf)

    column_filters = {
        "surf_parc": lambda col: col > 0.0  # fiboa validator requires area > 0.0
    }

    missing_schemas = {
        "properties": {
            "group_code": {"type": "string"},
        }
    }
