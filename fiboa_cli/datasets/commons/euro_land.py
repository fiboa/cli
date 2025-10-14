from fiboa_cli.conversion.fiboa_converter import FiboaBaseConverter
from fiboa_cli.datasets.commons.hcat import AddHCATMixin


class EuroLandBaseConverter(AddHCATMixin, FiboaBaseConverter):
    """
    Datasets have been published by the
    [Euroland project](https://europe-land.eu/news/harmonized-database-of-european-land-use-data-published/)
    as open data. See https://zenodo.org/records/14384070 for a list of open data sets.

    Use this base class to create converters based on the euroland repository
    Subclasses should still declare the required attributes from BaseConverter

    id = ""
    short_name = ""
    title = ""
    description = ""
    provider = ""
    """

    hcat_columns = {
        "EC_trans_n": "hcat:name_en",
        "EC_hcat_n": "hcat:name",
        "EC_hcat_c": "hcat:code",
    }

    columns = {
        "geometry": "geometry",
        "field_id": "id",
        "farm_id": "farm_id",
        "crop:code_list": "crop:code_list",
        "crop_code": "crop:code",
        "crop_name": "crop:name",
        "organic": "organic",
        "field_size": "metrics:area",
        # "crop_area": "crop_area",
    }
    license = "CC-BY-4.0"
    missing_schemas = {
        "properties": {
            "farm_id": {"type": "string"},
            "organic": {"type": "uint8", "enum": [0, 1, 2]},
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        provider = "Europe-LAND HE Project <https://doi.org/10.5281/zenodo.14230620>"
        self.provider = (f"{self.provider}, {provider}") if self.provider else provider
