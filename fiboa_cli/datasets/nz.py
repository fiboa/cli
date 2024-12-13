from ..convert_utils import BaseConverter
import pandas as pd


class NZCropConverter(BaseConverter):
    DATA_ACCESS = """Download manually from https://data.mfe.govt.nz/layer/105407-irrigated-land-area-raw-2020-update/"""

    id = "nz"
    short_name = "New Zealand"
    title = "Irrigated land area"
    description = """This dataset covers Irrigated Land. Adapted by Ministry for the Environment and Statistics
     New Zealand to provide for environmental reporting transparency

     The spatial data covers all mainland regions of New Zealand, with the exception of Nelson, which is not believed to
     contain significant irrigated areas. The spatial dataset is an update of the national dataset that was first
     created in 2017. The current update has incorporated data from the 2019 – 2020 irrigation season."""

    providers = [
        {
            "name": "NZ Ministry for the environment",
            "url": "https://environment.govt.nz/",
            "roles": ["producer"]
        },
        {
            "name": "Aqualinc Research Limited",
            "url": "https://environment.govt.nz/publications/national-irrigated-land-spatial-dataset-2020-update",
            "roles": ["licensor"]
        }
    ]
    license = "CC-BY-4.0"
    extensions = ['https://fiboa.github.io/administrative-division-extension/v0.1.0/schema.yaml']
    index_as_id = True
    columns = {
        "id": "id",
        "geometry": "geometry",
        "type": "type",
        "area_ha": "area",
        "yearmapped": "determination_datetime",
        "Region": "admin:subdivision",
    }
    column_migrations = {
        'yearmapped': lambda col: pd.to_datetime(col, format='%Y')
    }
    column_additions = {
        "admin:country_code": "NZ",
    }
    missing_schemas = {
        "properties": {
            "type": {
                "type": "string",
            },
            "admin:subdivision": {
                "type": "string",
            },
        }
    }
