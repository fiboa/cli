from ..convert_utils import convert as convert_
import pandas as pd
import numpy as np
from .commons.admin import add_admin

SOURCES = None
DATA_ACCESS = """
Data must be obtained from the Swiss open data portal at https://www.geodienste.ch/services/lwb_nutzungsflaechen .

One can filter on "Verfügbarkeit" == "Frei erhältlich" to select only the open data.
That leaves out Cantons AR, NW, OW, VD and LI as on this date (2014-11-12).
The downloaded data can be shared with a open_by license. See https://opendata.swiss/de/terms-of-use .

Use the `-i` CLI parameter to provide the data source.
Download the Open data response to a local gpkg file (use `.gpkg` as file extension).

fiboa convert ch -o swiss.parquet -i lwb_nutzungsflaechen_lv95/geopackage/lwb_nutzungsflaechen_v2_0_lv95.gpkg
"""

ID = "ch"
SHORT_NAME = "Switzerland"
TITLE = "Field boundaries for Switzerland"
DESCRIPTION = "The cropfields of Switzerland (Nutzungsflächen) are published per administrative subdivision called Canton."
PROVIDERS = [
    {
        "name": "Konferenz der kantonalen Geoinformations- und Katasterstellen",
        "url": "https://www.kgk-cgc.ch/",
        "roles": ["producer", "licensor"]
    }
]
LICENSE = {
    "title": "opendata.swiss terms of use",
    "href": "https://opendata.swiss/en/terms-of-use",
    "type": "text/html",
    "rel": "license"
}
COLUMNS = {
    'geometry': 'geometry',
    'id': 'id',
    'flaeche_m2': 'area',
    'admin:country_code': 'admin:country_code',
    'kanton': 'admin:subdivision_code',
    "nutzung": "crop_name",
    'bezugsjahr': 'determination_datetime'
}
EXTENSIONS = [
    'https://fiboa.github.io/administrative-division-extension/v0.1.0/schema.yaml'
]
ADD_COLUMNS = {
    'admin:country_code': 'CH'
}
COLUMN_FILTERS = {
    'ist_ueberlagernd': lambda col: col == False,
}
COLUMN_MIGRATIONS = {
    'flaeche_m2': lambda column: np.where(column>0, column/10000, 0.001),
    'bezugsjahr': lambda col: pd.to_datetime(col, format='%Y'),
}

MISSING_SCHEMAS = {
    'properties': {
        'crop_name': {
            'type': 'string'
        },
    }
}

def convert(output_file, cache = None, **kwargs):
    convert_(
        output_file, cache, SOURCES,
        COLUMNS, ID, TITLE, DESCRIPTION,
        license=LICENSE,
        extensions=EXTENSIONS,
        missing_schemas=MISSING_SCHEMAS,
        column_additions=ADD_COLUMNS,
        column_migrations=COLUMN_MIGRATIONS,
        column_filters=COLUMN_FILTERS,
        providers=PROVIDERS,
        index_as_id=True,
        fid_as_index=True,
        **kwargs
    )
