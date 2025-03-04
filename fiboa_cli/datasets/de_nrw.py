from .commons.admin import AdminConverterMixin
from ..convert_utils import BaseConverter


class Converter(AdminConverterMixin, BaseConverter):
    sources = "https://www.opengeodata.nrw.de/produkte/umwelt_klima/bodennutzung/landwirtschaft/LFK-AKTI_EPSG25832_Shape.zip"
    id = "de_nrw"
    admin_subdivision_code = "NW"
    short_name = "Germany, North Rhine-Westphalia"
    title = "Field boundaries for North Rhine-Westphalia (NRW), Germany"
    description = """A field block (German: "Feldblock") is a contiguous agricultural area surrounded by permanent boundaries, which is cultivated by one or more farmers with one or more crops, is fully or partially set aside or is fully or partially taken out of production."""
    license = "dl-de/by-2-0"
    providers = [
        {
            "name": "Land Nordrhein-Westfalen / Open.NRW",
            "url": "https://www.opengeodata.nrw.de/produkte/umwelt_klima/bodennutzung/landwirtschaft/",
            "roles": ["producer", "licensor"]
        }
    ]
    extensions = {
        "https://fiboa.github.io/inspire-extension/v0.2.0/schema.yaml",
        "https://fiboa.github.io/flik-extension/v0.1.0/schema.yaml"
    }
    columns = {
        'geometry': 'geometry',
        'ID': 'id',
        'INSPIRE_ID': 'inspire:id',
        'FLIK': 'flik',
        'GUELT_VON': 'determination_datetime',
        # TODO implement crop:code extension
        'NUTZ_CODE': 'nutz_code',
        'NUTZ_TXT': 'nutz_txt',
        'AREA_HA': 'area',
    }
    missing_schemas = {
        'properties': {
            'nutz_code': {'type': 'string'},
            'nutz_txt': {'type': 'string'}
        }
    }
