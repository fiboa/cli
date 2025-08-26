from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import EuroCropsConverterMixin


class Converter(EuroCropsConverterMixin, FiboaBaseConverter):
    ec_mapping_csv = "si_2021.csv"
    ec_year = 2021
    sources = {
        "https://zenodo.org/records/10118572/files/SI_2021.zip?download=1": ["SI_2021_EC21.shp"]
    }

    id = "ec_si"
    short_name = "Slovenia"
    title = "Field boundaries for Slovenia"
    description = "This dataset contains the field boundaries for all of Slovenia in 2021. The data was collected by the Slovenian government."

    providers = [
        {
            "name": "Ministrstvo za kmetijstvo, gozdarstvo in prehrano",
            "url": "https://rkg.gov.si/vstop/",
            "roles": ["producer", "licensor"],
        }
    ]
    attribution = "Ministrstvo za kmetijstvo, gozdarstvo in prehrano"

    columns = {
        "geometry": "geometry",
        "ID": "id",
        "AREA": "metrics:area",
        "GERK_PID": "gerk_pid",
        "SIFRA_KMRS": "crop_type_class",
        "RASTLINA": "rastlina",
        "CROP_LAT_E": "crop_lat_e",
        "COLOR": "color",
        "EC_NUTS3": "EC_NUTS3",
    }

    column_migrations = {"AREA": lambda column: column * 0.0001}

    missing_schemas = {
        "required": ["gerk_pid", "crop_type_class", "rastlina", "crop_lat_e", "color"],
        "properties": {
            "gerk_pid": {"type": "uint64"},
            "crop_type_class": {"type": "string"},
            "rastlina": {"type": "string"},
            "crop_lat_e": {"type": "string"},
            "color": {"type": "string"},
            "EC_NUTS3": {"type": "string"},
        },
    }

    def add_hcat(self, gdf):
        # skip adding hcat
        return gdf
