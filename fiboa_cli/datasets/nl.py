import pandas as pd
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin

# see https://service.pdok.nl/rvo/gewaspercelen/atom/basisregistratie_gewaspercelen_brp.xml
# (the old feed rvo/brpgewaspercelen/atom/v1_0/ redirects here since 2026)
base = "https://service.pdok.nl/rvo/gewaspercelen/atom/downloads"

# RVO gave these codes a new crop from the year listed. Earlier editions get the
# code with an "o" suffix, which the code list carries with the old meaning, so
# the current list holds for every edition. 2636 (landscape element → Leibomen,
# year unknown) is left out: landscape elements are filtered out.
REUSED_CODES = {
    "1926": 2016,
    "1927": 2017,
    "657": 2019,
    "1932": 2019,
    "1933": 2019,
    "1934": 2019,
    "1935": 2019,
}


class NLCropConverter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    variants = {
        "2026": f"{base}/gewaspercelen_concept_2026.gpkg",
        **{str(y): f"{base}/brpgewaspercelen_definitief_{y}.gpkg" for y in range(2025, 2019, -1)},
        # the zip editions each contain one FileGDB (naming varies per year)
        **{
            str(y): {f"{base}/brpgewaspercelen_definitief_{y}.zip": ["*.gdb"]}
            for y in range(2019, 2008, -1)
        },
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

<https://service.pdok.nl/rvo/gewaspercelen/atom/index.xml>

Data is currently available for the years 2009 to 2025 (final) and 2026 (concept).
    """

    provider = (
        "RVO / PDOK <https://www.pdok.nl/introductie/-/article/basisregistratie-gewaspercelen-brp->"
    )
    # Both http://creativecommons.org/publicdomain/zero/1.0/deed.nl and http://creativecommons.org/publicdomain/mark/1.0/
    license = "CC0-1.0"

    columns = {
        "geometry": "geometry",
        "category": "coverage",
        "gewascode": "crop:code",
        "gewas": "crop:name",
        "jaar": "determination:datetime",
    }

    def migrate(self, gdf):
        if "GWS_GEWASCODE" in gdf.columns:
            # 2009-2019 FileGDB editions: prefixed names, no year column, and
            # only a m2 shape area (left unmapped; metrics:area is measured
            # from the geometry instead)
            gdf = gdf.rename(
                columns={
                    "GWS_GEWASCODE": "gewascode",
                    "GWS_GEWAS": "gewas",
                    "CAT_GEWASCATEGORIE": "category",
                }
            )
            gdf["jaar"] = int(self.variant)
        codes = gdf["gewascode"].astype(str).str.strip()
        old = [code for code, year in REUSED_CODES.items() if int(self.variant) < year]
        gdf["gewascode"] = codes.mask(codes.isin(old), codes + "o")
        return super().migrate(gdf)

    column_filters = {
        # category = "Grasland" | "Bouwland" | "Sloot" | "Landschapselement"
        "category": lambda col: col.isin(["Grasland", "Bouwland"])
    }

    column_migrations = {
        # Add 15th of may to original "year" (jaar) column
        "jaar": lambda col: pd.to_datetime(col, format="%Y") + pd.DateOffset(months=4, days=14)
    }
    extensions = {"https://fiboa.org/crop-extension/v0.2.0/schema.yaml"}
    hcat_mapping_csv = "https://fiboa.org/code/nl/nl.csv"

    missing_schemas = {
        "properties": {
            "coverage": {"type": "string", "enum": ["Grasland", "Bouwland"]},
        }
    }
