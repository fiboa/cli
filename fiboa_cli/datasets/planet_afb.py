# Converter for geopackage output of Planet's Field Boundaries dataset.
import os
import re

from ..conversion.fiboa_converter import FiboaBaseConverter


class Converter(FiboaBaseConverter):
    sources = None
    data_access = """
    Data must be obtained from the Planet subscriptions API, see
    https://developers.planet.com/docs/planetary-variables/field-boundaries/ for additional information.
    The output should look something like FIELD_BOUNDARIES_v1.0.0_S2_P1M-20230101T000000Z_fb.gpkg
    """
    id = "planet_afb"
    short_name = "Planet Field Boundaries"
    title = "Field boundaries created by Planet's Automated Field Boundary detection algorithm"
    description = """
    These field boundaries are created by Planet Labs, using an automated process using satellite imagery. The algorithm
    works on a monthly basis and is available for the entire globe. The data is provided in GeoPackage format.
    For more information, see the [field boundaries technical specification](https://planet.widen.net/s/5vq8w5wjvf/2403.08_mar-9444-field-boundaries-technical-specification-sheet-3)
    """
    providers = [
        {"name": "Planet Labs, PBC", "url": "https://planet.com", "roles": ["producer", "licensor"]}
    ]
    attribution = "© 2024 Planet Labs, PBC"
    license = {
        "title": "Proprietary License",
        "href": "https://www.planet.com/licensing-information/",
        "type": "text/html",
        "rel": "license",
    }
    extensions = {"https://fiboa.github.io/planet-extension/v0.1.0/schema.yaml"}
    columns = {
        "polygon_id": "id",  # fiboa core field
        "area_ha": "metrics:area",  # fiboa core field
        "geometry": "geometry",  # fiboa core field
        "determination:datetime": "determination:datetime",  # fiboa core field
        "ca_ratio": "planet:ca_ratio",  # From Planet extension for fiboa
        "micd": "planet:micd",  # From Planet extension for fiboa
        "qa": "planet:qa",  # From Planet extension for fiboa
    }
    column_additions = {"determination_method": "auto-imagery"}
    missing_schemas = {}

    def file_migration(self, gdf, path, uri, layer=None):
        """
        Perform file-specific migration by extracting a date from the filename and adding it as a column in the GeoDataFrame.

        Assumed filename format:
        FIELD_BOUNDARIES_v1.0.0_S2_P1M-20230101T000000Z_fb.gpkg
        """
        name = os.path.basename(path)
        matches = re.search(r"-(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z_fb.gpkg$", name)
        if matches:
            dt = matches.groups()
            gdf["determination:datetime"] = f"{dt[0]}-{dt[1]}-{dt[2]}T{dt[3]}:{dt[4]}:{dt[5]}Z"
        return gdf
