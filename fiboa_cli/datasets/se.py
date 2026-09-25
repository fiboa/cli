import pandas as pd
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin

# One WFS layer holds every campaign; the year is a filter, not a layer. The
# service answers 2015 through 2025 (2014 and 2026 return zero features), and
# redirects http to https, so ask for https to save a round trip.
WFS = (
    "https://epub.sjv.se/inspire/inspire/wfs?SERVICE=WFS&REQUEST=GetFeature&VERSION=2.0.0"
    "&TYPENAMES=inspire:arslager_skifte&outputFormat=shape-zip"
    "&CQL_FILTER=arslager=%27{year}%27%20and%20geom%20is%20not%20null"
    "&format_options=CHARSET:UTF-8"
)


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    # the response has no usable file name, so each edition names its own
    variants = {
        str(year): {WFS.format(year=year): f"se{year}.zip"} for year in range(2025, 2014, -1)
    }
    id = "se"
    short_name = "Sweden"
    title = "Swedish Crop Fields (Jordbruksskiften)"
    description = """
A crop field (Jordbruksskift) is a contiguous area of land within a block where a farmer grows a crop or otherwise manages the land.
To receive compensation for agricultural support (EU support), farmers apply for support from the
Swedish Agency for Agriculture via a SAM application. The data set contains parcels where the area
applied for and the area decided on are the same. The data is published at the end of a year.

    Codes found at https://jordbruksverket.se/stod/jordbruk-tradgard-och-rennaring/sam-ansokan-och-allmant-om-jordbrukarstoden/grodkoder
    """
    provider = "Jordbruksverket (The Swedish Board of Agriculture) <https://jordbruksverket.se>"
    attribution = "Jordbruksverket"
    license = "CC0-1.0"  # "Open Data"
    columns = {
        "geometry": "geometry",
        "faststalld": "metrics:area",
        "grdkod_mar": "crop:code",
        "arslager": "determination:datetime",
    }
    extensions = {"https://fiboa.org/crop-extension/v0.2.0/schema.yaml"}
    hcat_mapping_csv = "https://fiboa.org/code/se/se.csv"
    column_migrations = {
        # the campaign year, as an integer in the shapefile
        "arslager": lambda col: pd.to_datetime(col.astype(str), format="%Y")
    }

    # A skifte is one crop inside a block, numbered within it ("1A", "54B"), so
    # the field is the pair.
    id_columns = ("blockid", "skiftesbet")
    id_separator = "_"
