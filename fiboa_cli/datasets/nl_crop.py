from ..convert_utils import convert as convert_
from .commons.admin import add_admin
import pandas as pd


SOURCES = "https://service.pdok.nl/rvo/brpgewaspercelen/atom/v1_0/downloads/brpgewaspercelen_concept_2023.gpkg"

ID = "nl_crop"
SHORT_NAME = "Netherlands (Crops)"
TITLE = "BRP Crop Field Boundaries for The Netherlands (CAP-based)"
DESCRIPTION = """
"BasisRegistratiePercelen" (BRP) combines the location of
agricultural plots with the crop grown. The data set
is published by RVO (Netherlands Enterprise Agency). The boundaries of the agricultural plots
are based within the reference parcels (formerly known as AAN). A user an agricultural plot
annually has to register his crop fields with crops (for the Common Agricultural Policy scheme).
A dataset is generated for each year with reference date May 15.
A view service and a download service are available for the most recent BRP crop plots.

<https://service.pdok.nl/rvo/brpgewaspercelen/atom/v1_0/index.xml>

Data is currently available for the years 2009 to 2023.
"""

PROVIDERS = [
    {
        "name": "RVO / PDOK",
        "url": "https://www.pdok.nl/introductie/-/article/basisregistratie-gewaspercelen-brp-",
        "roles": ["producer", "licensor"]
    }
]
ATTRIBUTION = None
# Both http://creativecommons.org/publicdomain/zero/1.0/deed.nl and http://creativecommons.org/publicdomain/mark/1.0/
LICENSE = "CC0-1.0"

COLUMNS = {
    'geometry': 'geometry',
    'id': 'id',
    'area': "area",
    'category': 'category',
    'gewascode': 'crop_code',
    'gewas': 'crop_name',
    'jaar': 'determination_datetime'
}

COLUMN_FILTERS = {
    # category = "Grasland" | "Bouwland" | "Sloot" | "Landschapselement"
    'category': lambda col: col.isin(["Grasland", "Bouwland"])
}

COLUMN_MIGRATIONS = {
    # Add 15th of may to original "year" (jaar) column
    'jaar': lambda col: pd.to_datetime(col, format='%Y') + pd.DateOffset(months=4, days=14)
}


def migrate(gdf):
    # Projection is in CRS 28992 (RD New), this is the area calculation method of the source organization
    # todo: remove in favor of generic solution for area calculation
    gdf['area'] = gdf.area / 10000
    return gdf


MIGRATION = migrate

MISSING_SCHEMAS = {
    "properties": {
        "category": {
            "type": "string",
            "enum": ["Grasland", "Bouwland"]
        },
        "crop_name": {
            "type": "string"
        },
        "crop_code": {
            "type": "string"
        },
    }
}

COLUMNS, ADD_COLUMNS, EXTENSIONS = add_admin(vars(), "NL")


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
        column_migrations=COLUMN_MIGRATIONS,
        migration=MIGRATION,
        attribution=ATTRIBUTION,
        license=LICENSE,
        index_as_id=True,
        **kwargs
    )
