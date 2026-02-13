import pandas as pd
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin

# see https://service.pdok.nl/rvo/brpgewaspercelen/atom/v1_0/basisregistratie_gewaspercelen_brp.xml
base = "https://service.pdok.nl/rvo/brpgewaspercelen/atom/v1_0/downloads"


class NLCropConverter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    area_calculate_missing = True
    variants = {
        "2025": f"{base}/brpgewaspercelen_concept_2025.gpkg",
        **{str(y): f"{base}/brpgewaspercelen_definitief_{y}.gpkg" for y in range(2024, 2020, -1)},
        **{str(y): f"{base}/brpgewaspercelen_definitief_{y}.zip" for y in range(2020, 2009, -1)},
    }

    id = "nl"
    short_name = "Netherlands (Crops)"
    title = "BRP Crop Field Boundaries for The Netherlands (CAP-based)"
    description = """
BasisRegistratie Percelen (BRP) combines the location of
agricultural plots with the crop grown. The data set
is published by RVO (Netherlands Enterprise Agency). The boundaries of the agricultural plots
are based within the reference parcels (formerly known as AAN). A user an agricultural plot
annually has to register his crop fields with crops (for the Common Agricultural Policy scheme).
A dataset is generated for each year with reference date May 15.
A view service and a download service are available for the most recent BRP crop plots.

<https://service.pdok.nl/rvo/brpgewaspercelen/atom/v1_0/index.xml>

Data is currently available for the years 2009 to 2024.
    """

    provider = (
        "RVO / PDOK <https://www.pdok.nl/introductie/-/article/basisregistratie-gewaspercelen-brp->"
    )
    # Both http://creativecommons.org/publicdomain/zero/1.0/deed.nl and http://creativecommons.org/publicdomain/mark/1.0/
    license = "CC0-1.0"

    columns = {
        "geometry": "geometry",
        "id": "id",
        "area": "metrics:area",
        "category": "coverage",
        "gewascode": "crop:code",
        "gewas": "crop:name",
        "jaar": "determination:datetime",
    }

    column_filters = {
        # category = "Grasland" | "Bouwland" | "Sloot" | "Landschapselement"
        "category": lambda col: col.isin(["Grasland", "Bouwland"])
    }

    column_migrations = {
        # Add 15th of may to original "year" (jaar) column
        "jaar": lambda col: pd.to_datetime(col, format="%Y") + pd.DateOffset(months=4, days=14)
    }
    extensions = {"https://fiboa.org/crop-extension/v0.2.0/schema.yaml"}
    ec_mapping_csv = "https://fiboa.org/code/nl/nl.csv"
    index_as_id = True

    missing_schemas = {
        "properties": {
            "coverage": {"type": "string", "enum": ["Grasland", "Bouwland"]},
        }
    }
