from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    sources = "https://data.geobasis-bb.de/geofachdaten/Landwirtschaft/antrag.zip"
    id = "de_bb"
    admin_subdivision_code = "BB"  # TODO Berlin is also in here, check each row
    short_name = "Germany, Berlin/Brandenburg"
    title = "Field boundaries for Berlin / Brandenburg, Germany"
    description = """A Crop Field (German: "Schlaege") is a contiguous agricultural area surrounded by permanent boundaries, which is cultivated with a single crop."""
    license = "DL-DE-BY-2.0"
    provider = "Land Brandenburg <https://geobroker.geobasis-bb.de/gbss.php?MODE=GetProductInformation&PRODUCTID=9e95f21f-4ecf-4682-9a44-e5f7609f6fa0>"
    ec_mapping_csv = "de.csv"

    columns = {
        "geometry": "geometry",
        "ref_ident": "farmer_id",
        "groesse": "metrics:area",
        "guelt_von": "determination:datetime",
        "code_bez": "crop:name",
        "code": "crop:code",
    }
    missing_schemas = {
        "properties": {
            "farmer_id": {"type": "string"},
        }
    }
    column_migrations = {"code": lambda col: col.fillna("").astype(str)}
