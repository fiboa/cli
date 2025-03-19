from ..convert_utils import convert as convert_
from .commons.ec import add_eurocrops

SOURCES = {"https://zenodo.org/records/10118572/files/SI_2021.zip?download=1": ["SI_2021_EC21.shp"]}

ID = "ec_si"
SHORT_NAME = "Slovenia"
TITLE = "Field boundaries for Slovenia"
DESCRIPTION = "This dataset contains the field boundaries for all of Slovenia in 2021. The data was collected by the Slovenian government."

PROVIDERS = [
    {
        "name": "Ministrstvo za kmetijstvo, gozdarstvo in prehrano",
        "url": "https://rkg.gov.si/vstop/",
        "roles": ["producer", "licensor"],
    }
]
ATTRIBUTION = "Ministrstvo za kmetijstvo, gozdarstvo in prehrano"

COLUMNS = {
    "geometry": "geometry",
    "ID": "id",
    "AREA": "area",
    "GERK_PID": "gerk_pid",
    "SIFRA_KMRS": "crop_type_class",
    "RASTLINA": "rastlina",
    "CROP_LAT_E": "crop_lat_e",
    "COLOR": "color",
    "EC_NUTS3": "EC_NUTS3",
}

COLUMN_MIGRATIONS = {"AREA": lambda column: column * 0.0001}

MISSING_SCHEMAS = {
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

ID, SHORT_NAME, TITLE, DESCRIPTION, PROVIDERS, EXTENSIONS, COLUMNS, LICENSE = add_eurocrops(
    vars(), 2021
)


def convert(output_file, cache=None, **kwargs):
    convert_(
        output_file,
        cache,
        SOURCES,
        COLUMNS,
        ID,
        TITLE,
        DESCRIPTION,
        extensions=EXTENSIONS,
        providers=PROVIDERS,
        missing_schemas=MISSING_SCHEMAS,
        column_migrations=COLUMN_MIGRATIONS,
        attribution=ATTRIBUTION,
        license=LICENSE,
        **kwargs,
    )
