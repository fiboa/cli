from fiboa_cli.convert_utils import BaseConverter


class EuroLandBaseConverter(BaseConverter):
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
    providers = []

    # And additionally declare a crop_code_list
    crop_code_list = ec_url(ec_mapping_csv)
    """

    crop_code_list = None  # e.g. ec_url(ec_mapping_csv)
    extensions = {
        "https://fiboa.github.io/crop-extension/v0.1.0/schema.yaml",
        "https://fiboa.github.io/hcat-extension/v0.1.0/schema.yaml",
    }
    columns = {
        "geometry": "geometry",
        "field_id": "id",
        "farm_id": "farm_id",
        "crop:code_list": "crop:code_list",
        "crop_code": "crop:code",
        "crop_name": "crop:name",
        "EC_trans_n": "ec:translated_name",
        "EC_hcat_n": "ec:hcat_name",
        "EC_hcat_c": "ec:hcat_code",
        "organic": "organic",
        "field_size": "area",
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
        assert self.crop_code_list, f"Please declare a crop_code_list attribute on {self.__class__}"
        self.column_additions["crop:code_list"] = self.crop_code_list
        self.providers.append(
            {
                "name": "Europe-LAND HE Project",
                "url": "https://doi.org/10.5281/zenodo.14230620",
                "roles": ["processor"],
            }
        )
