import geopandas as gpd
import pandas as pd

from ..convert_utils import BaseConverter
from .commons.admin import AdminConverterMixin
from .commons.ec import ec_url

# see https://service.pdok.nl/rvo/brpgewaspercelen/atom/v1_0/basisregistratie_gewaspercelen_brp.xml
base = "https://service.pdok.nl/rvo/brpgewaspercelen/atom/v1_0/downloads"


class NLCropConverter(AdminConverterMixin, BaseConverter):
    years = {
        2024: f"{base}/brpgewaspercelen_concept_2024.gpkg",
        2023: f"{base}/brpgewaspercelen_definitief_2023.gpkg",
        2022: f"{base}/brpgewaspercelen_definitief_2022.gpkg",
        2021: f"{base}/brpgewaspercelen_definitief_2021.gpkg",
        2020: f"{base}/brpgewaspercelen_definitief_2020.gpkg",
        # {r: {base}/brpgewaspercelen_definitief_{r}.zip for r in range(2009, 2020)}
    }

    id = "nl_crop"
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

    providers = [
        {
            "name": "RVO / PDOK",
            "url": "https://www.pdok.nl/introductie/-/article/basisregistratie-gewaspercelen-brp-",
            "roles": ["producer", "licensor"],
        }
    ]
    # Both http://creativecommons.org/publicdomain/zero/1.0/deed.nl and http://creativecommons.org/publicdomain/mark/1.0/
    license = "CC0-1.0"

    columns = {
        "geometry": "geometry",
        "id": "id",
        "area": "area",
        "category": "category",
        "gewascode": "crop:code",
        "gewas": "crop:name",
        "jaar": "determination_datetime",
    }

    column_filters = {
        # category = "Grasland" | "Bouwland" | "Sloot" | "Landschapselement"
        "category": lambda col: col.isin(["Grasland", "Bouwland"])
    }

    column_migrations = {
        # Add 15th of may to original "year" (jaar) column
        "jaar": lambda col: pd.to_datetime(col, format="%Y") + pd.DateOffset(months=4, days=14)
    }
    extensions = {"https://fiboa.github.io/crop-extension/v0.1.0/schema.yaml"}
    column_additions = {"crop:code_list": ec_url("nl_2020.csv")}
    index_as_id = True

    def migrate(self, gdf) -> gpd.GeoDataFrame:
        # Projection is in CRS 28992 (RD New), this is the area calculation method of the source organization
        # todo: remove in favor of generic solution for area calculation
        gdf["area"] = gdf.area / 10000
        return gdf

    missing_schemas = {
        "properties": {
            "category": {"type": "string", "enum": ["Grasland", "Bouwland"]},
        }
    }
