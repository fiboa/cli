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
            "https://data.geopf.fr/telechargement/download/RPG/RPG_2-0__GPKG_LAMB93_FR_2020-01-01/RPG_2-0__GPKG_LAMB93_FR_2020-01-01.7z.001": [],
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
    # The 2018 code list does not cover the codes RPG added later, and the
    # editions we publish run to 2024: MLC, MLF, HPC and ACP alone account for
    # 37,011 fields of the 2024 edition.
    ec_mapping_supplements = [
        "fr_other_years.csv",
        # Codes neither EuroCrops table carries, mapped from the sibling code
        # each one has there: JAC (jachère) alone is 604,122 fields of 2024.
        "https://fiboa.org/code/fr/fr_supplement.csv",
    ]
    use_variant_as_determination = True

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

        # RPG's own parcel id identifies a field in every edition but 2024,
        # where 361 ids cover 736 of the 9,679,888 rows: 231 of those rows are
        # exact duplicates and the rest are two declarations sharing one id
        # (10308017 is declared both BOR and PTR). It is published as
        # `parcel_id` throughout, and `id` falls back to the row index in an
        # edition where it repeats — safe, because an edition is one layer of
        # one file.
        gdf["parcel_id"] = gdf["id_parcel"]
        if gdf["id_parcel"].is_unique:
            gdf["id"] = gdf["id_parcel"]
        else:
            repeats = len(gdf) - gdf["id_parcel"].nunique()
            self.warning(
                f"id_parcel repeats for {repeats:,} of {len(gdf):,} rows in this edition; "
                "numbering the rows and keeping it as parcel_id"
            )
            gdf["id"] = gdf.index
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
