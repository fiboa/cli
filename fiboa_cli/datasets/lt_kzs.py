from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.converter_rest import EsriRESTConverterMixin
from ..conversion.fiboa_converter import FiboaBaseConverter


class LTKZSConverter(AdminConverterMixin, EsriRESTConverterMixin, FiboaBaseConverter):
    id = "lt_kzs"
    short_name = "Lithuania, KŽS"
    title = "Reference parcels (Lithuania, KŽS)"
    description = """
KŽS (Kontroliniai žemės sklypai) is Lithuania's Land Parcel Identification System
(LPIS), maintained at scale 1:5000 as part of the Integrated Administration and
Control System (IACS).

This converter reads the blocks eligible for support (GKODAS `bl1` and `bl1b`),
269,355 of the 2,150,085 polygons published by the service. The remainder describe
ineligible land, forest, hydrography and landscape elements.

The dataset carries no crop information; crop declarations are published separately.
"""

    provider = "VĮ Žemės ūkio duomenų centras <https://www.zudc.lt>"
    attribution = "© VĮ Žemės ūkio duomenų centras"
    license = (
        "Copyright, no reuse licence stated "
        "<https://www.geoportal.lt/metadata-catalog/catalog/search/resource/details.page?uuid=%7B5266D059-0781-4650-9BF6-B2618CF2915E%7D>"
    )

    rest_base_url = (
        "https://www.geoportal.lt/arcgis/rest/services/nma/KZS5LT_kontroliniai_sklypai/MapServer"
    )

    rest_format = "json"
    rest_params = {"where": "GKODAS IN ('bl1','bl1b')", "outSR": "4326"}

    area_is_in_ha = False  # Shape_Area is in m², not ha

    columns = {
        "OBJECTID": "id",
        "geometry": "geometry",
        "BLOKAS_ID": "blokas_id",
        "GKODAS": "gkodas",
        "Shape_Area": "metrics:area",
        "Shape_Length": "metrics:perimeter",
    }

    column_migrations = {"OBJECTID": lambda col: col.astype(str)}

    missing_schemas = {
        "properties": {
            "blokas_id": {"type": "string"},
            "gkodas": {"type": "string"},
        }
    }
