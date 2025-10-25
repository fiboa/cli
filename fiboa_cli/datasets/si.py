from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    sources = {"https://rkg.gov.si/razno/portal_analysis/KMRS_2023.rar": ["KMRS_2023.shp"]}
    id = "si"
    short_name = "Slovenia"
    title = "Slovenia Crop Fields"
    description = """
    The Slovenian government provides slightly different, relevant open data sets called GERK, KMRS, RABA and EKRZ.
    This converter uses the KRMS dataset, which includes CAP applications of the last year and discerns
    around 150 different crop categories.
    """
    provider = "Ministry of Agriculture, Forestry and Food (Ministrstvo za kmetijstvo, gozdarstvo in prehrano) <https://www.gov.si/drzavni-organi/ministrstva/ministrstvo-za-kmetijstvo-gozdarstvo-in-prehrano/>"

    license = "Javno dostopni podatki: Publicly available data <https://rkg.gov.si/vstop/>"

    columns = {
        "geometry": "geometry",
        "ID": "id",
        "GERK_PID": "block_id",
        "AREA": "metrics:area",
        "SIFRA_KMRS": "crop:code",
        "RASTLINA": "crop:name",
        "CROP_LAT_E": "crop:name_en",
    }
    ec_mapping_csv = "si_2021.csv"
    column_migrations = {"geometry": lambda col: col.make_valid()}
    area_is_in_ha = False
    missing_schemas = {
        "properties": {
            "block_id": {"type": "uint64"},
        }
    }
