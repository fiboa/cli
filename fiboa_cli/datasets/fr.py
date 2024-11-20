from ..convert_utils import convert as convert_
from .commons.admin import add_admin

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
ATTRIBUTION = "IGN — Original data from https://geoservices.ign.fr/rpg"
LICENSE = {"title": "Licence Ouverte / Open Licence", "href": "https://etalab.gouv.fr/licence-ouverte-open-licence", "type": "text/html", "rel": "license"}

COLUMNS = {
    'geometry': 'geometry',
    'id_parcel': 'id',
    'surf_parc': 'area',
    'code_cultu': 'crop_code',
    'code_group': 'group_code',
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

COLUMNS, ADD_COLUMNS, EXTENSIONS = add_admin(vars(), "FR")

def convert(output_file, cache = None, **kwargs):
    convert_(
        output_file,
        cache,
        SOURCES,
        COLUMNS,
        ID,
        TITLE,
        DESCRIPTION,
        providers=PROVIDERS,
        extensions=EXTENSIONS,
        missing_schemas=MISSING_SCHEMAS,
        column_additions=ADD_COLUMNS,
        column_filters=COLUMN_FILTERS,
        attribution=ATTRIBUTION,
        license=LICENSE,
        **kwargs
    )
