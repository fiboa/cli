from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import AddHCATMixin


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    sources = "https://www.opengeodata.nrw.de/produkte/umwelt_klima/bodennutzung/landwirtschaft/LFK-AKTI_EPSG25832_Shape.zip"
    id = "de_nrw"
    admin_subdivision_code = "NW"
    short_name = "Germany, North Rhine-Westphalia"
    title = "Field boundaries for North Rhine-Westphalia (NRW), Germany"
    description = """A field block (German: "Feldblock") is a contiguous agricultural area surrounded by permanent boundaries, which is cultivated by one or more farmers with one or more crops, is fully or partially set aside or is fully or partially taken out of production."""
    license = "DL-DE-BY-2.0"
    provider = "Land Nordrhein-Westfalen / Open.NRW <https://www.opengeodata.nrw.de/produkte/umwelt_klima/bodennutzung/landwirtschaft/>"
    extensions = {
        "https://fiboa.org/inspire-extension/v0.3.0/schema.yaml",
        "https://fiboa.org/flik-extension/v0.2.0/schema.yaml",
    }
    ec_mapping_csv = "de_nrw_2021.csv"
    columns = {
        "geometry": "geometry",
        "ID": "id",
        "INSPIRE_ID": "inspire:id",
        "FLIK": "flik",
        "GUELT_VON": "determination:datetime",
        "NUTZ_CODE": "crop:code",
        "NUTZ_TXT": "crop:name",
        "AREA_HA": "metrics:area",
    }
