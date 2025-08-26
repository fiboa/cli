import pandas as pd

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import EuroCropsConverterMixin

# todo: The dataset doesn't validate due to a self intersecting polygon
# How do we want to handle this?


class Convert(EuroCropsConverterMixin, FiboaBaseConverter):
    ec_mapping_csv = "ee_2021.csv"
    ec_year = 2021
    sources = "https://zenodo.org/records/14094196/files/EE_2021.zip?download=1"
    id = "ec_ee"
    short_name = "Estonia"
    title = "Field boundaries for Estonia"
    description = """
    Geospatial Aid Application Estonia Agricultural parcels.
    The original dataset is provided by ARIB and obtained from the INSPIRE theme GSAA (specifically Geospaial Aid Application Estonia Agricultural parcels) through which the data layer Fields and Eco Areas (GSAA) is made available.
    The data comes from ARIB's database of agricultural parcels.
    """
    providers = [
        {
            "name": "Põllumajanduse Registrite ja Informatsiooni Amet",
            "url": "http://data.europa.eu/88u/dataset/pria-pollud",
            "roles": ["producer", "licensor"],
        }
    ]
    attribution = "© Põllumajanduse Registrite ja Informatsiooni Amet"

    columns = {
        "geometry": "geometry",
        "pollu_id": "id",
        "taotlusaas": "determination:datetime",  # year
        "pindala_ha": "metrics:area",  # area (in ha)
        "taotletud_": "crop:code",  # requested crop culture
        "taotletu_1": "taotletud_maakasutus",  # requested land use
        "taotletu_2": "taotletud_toetus",  # requested support
        "niitmise_t": "niitmise_tuvastamise_staatus",  # mowing detection status
        "niitmise_1": "niitmise_tuvast_ajavahemik",  # mowing detection period
        "viimase_mu": "viimase_muutmise_aeg",  # Last edit time (date-date)
        "taotleja_n": "taotleja_nimi",  # name of applicant
        "taotleja_r": "taotleja_registrikood",  # applicant's registration code
    }
    column_migrations = {"JAHR": lambda col: pd.to_datetime(col, format="%Y")}
    missing_schemas = {
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
