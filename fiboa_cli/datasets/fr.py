from ..convert_utils import convert as convert_

SOURCES = {
    "https://data.geopf.fr/telechargement/download/RPG/RPG_2-0__GPKG_LAMB93_FXX_2022-01-01/RPG_2-0__GPKG_LAMB93_FXX_2022-01-01.7z.001": [
        "RPG_2-0__GPKG_LAMB93_FXX_2022-01-01/RPG/1_DONNEES_LIVRAISON_2023-08-01/RPG_2-0_GPKG_LAMB93_FXX-2022/PARCELLES_GRAPHIQUES.gpkg"
    ]
}
ID = "fr"
SHORT_NAME = "France"
TITLE = "Registre Parcellaire Graphique; Crop Fields France"
DESCRIPTION = """
France has published Crop Field data for many years. Crop fields are declared by farmers within the Common Agricultural Policy (CAP) subsidy scheme.

The anonymized version is distributed as part of the public service for making reference data available contains graphic data for plots (basic land unit for farmers' declaration) with their main crop. This data has been produced by the Services and Payment Agency (ASP) since 2007.
"""

PROVIDERS = [
    {
        "name": "Anstitut National de l'Information Géographique et Forestière",
        "url": "https://www.data.gouv.fr/en/datasets/registre-parcellaire-graphique-rpg-contours-des-parcelles-et-ilots-culturaux-et-leur-groupe-de-cultures-majoritaire/",
        "roles": ["producer", "licensor"]
    }
]
# Attribution example as described in the open license
ATTRIBUTION = "IGN — Original data downloaded from https://geoservices.ign.fr/rpg, updated on June 14 2024"
LICENSE = {"title": "Licence Ouverte / Open Licence", "href": "https://etalab.gouv.fr/licence-ouverte-open-licence", "type": "text/html", "rel": "license"}

COLUMNS = {
    'geometry': 'geometry',
    'id_parcel': 'id',
    'surf_parc': 'area',
    'code_cultu': 'crop_code',
    'code_group': 'group_code',
}

ADD_COLUMNS = {
    "determination_datetime": "2022-01-15T00:00:00Z"
}

COLUMN_FILTERS = {
    "surf_parc": lambda col: col > 0.0  # fiboa validator requires area > 0.0
}
MISSING_SCHEMAS = {
    "properties": {
        "crop_code": {
            "type": "string"
        },
        "group_code": {
            "type": "string"
        },
    }
}


def convert(output_file, input_files = None, cache = None, source_coop_url = None, collection = False, compression = None):
    convert_(
        output_file,
        cache,
        SOURCES,
        COLUMNS,
        ID,
        TITLE,
        DESCRIPTION,
        input_files=input_files,
        providers=PROVIDERS,
        source_coop_url=source_coop_url,
        missing_schemas=MISSING_SCHEMAS,
        column_additions=ADD_COLUMNS,
        column_filters=COLUMN_FILTERS,
        attribution=ATTRIBUTION,
        store_collection=collection,
        license=LICENSE,
        compression=compression,
        explode_multipolygon=True
    )
