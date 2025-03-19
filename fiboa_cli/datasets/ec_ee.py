import pandas as pd

from ..convert_utils import convert as convert_
from .commons.ec import add_eurocrops

# todo: The dataset doesn't validate due to a self intersecting polygon
# How do we want to handle this?

SOURCES = "https://zenodo.org/records/8229128/files/EE_2021.zip?download=1"

ID = "ec_ee"
SHORT_NAME = "Estonia"
TITLE = "Field boundaries for Estonia"
DESCRIPTION = """
Geospatial Aid Application Estonia Agricultural parcels.
The original dataset is provided by ARIB and obtained from the INSPIRE theme GSAA (specifically Geospaial Aid Application Estonia Agricultural parcels) through which the data layer Fields and Eco Areas (GSAA) is made available.
The data comes from ARIB's database of agricultural parcels.
"""
PROVIDERS = [
    {
        "name": "Põllumajanduse Registrite ja Informatsiooni Amet",
        "url": "http://data.europa.eu/88u/dataset/pria-pollud",
        "roles": ["producer", "licensor"],
    }
]
ATTRIBUTION = "© Põllumajanduse Registrite ja Informatsiooni Amet"

COLUMNS = {
    "geometry": "geometry",
    "pollu_id": "id",
    "taotlusaas": "determination_datetime",  # year
    "pindala_ha": "area",  # area (in ha)
    "taotletud_": "taotletud_kultuur",  # requested crop culture
    "taotletu_1": "taotletud_maakasutus",  # requested land use
    "taotletu_2": "taotletud_toetus",  # requested support
    "niitmise_t": "niitmise_tuvastamise_staatus",  # mowing detection status
    "niitmise_1": "niitmise_tuvast_ajavahemik",  # mowing detection period
    "viimase_mu": "viimase_muutmise_aeg",  # Last edit time (date-date)
    "taotleja_n": "taotleja_nimi",  # name of applicant
    "taotleja_r": "taotleja_registrikood",  # applicant's registration code
}
COLUMN_MIGRATIONS = {"JAHR": lambda col: pd.to_datetime(col, format="%Y")}
MISSING_SCHEMAS = {
    "required": [
        "taotletud_kultuur",
        "taotletud_maakasutus",
        "viimase_muutmise_aeg",
        "taotleja_nimi",
    ],
    "properties": {
        "taotletud_kultuur": {"type": "string"},
        "taotletud_maakasutus": {"type": "string"},
        "niitmise_tuvastamise_staatus": {"type": "string"},
        "niitmise_tuvast_ajavahemik": {"type": "string"},
        "viimase_muutmise_aeg": {"type": "string"},
        "taotletud_toetus": {"type": "string"},
        "taotleja_nimi": {"type": "string"},
        "taotleja_registrikood": {"type": "string"},
    },
}

ID, SHORT_NAME, TITLE, DESCRIPTION, PROVIDERS, EXTENSIONS, COLUMNS, LICENSE = add_eurocrops(
    vars(), 2021
)


def convert(output_file, cache=None, **kwargs):
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
        column_migrations=COLUMN_MIGRATIONS,
        missing_schemas=MISSING_SCHEMAS,
        attribution=ATTRIBUTION,
        license=LICENSE,
        **kwargs,
    )
