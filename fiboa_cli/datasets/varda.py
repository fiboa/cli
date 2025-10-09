# Converter for Varda field boundary datasets to Fiboa.
# Aiming to have it work with both direct API access and with bulk download.

from ..conversion.fiboa_converter import FiboaBaseConverter


class Converter(FiboaBaseConverter):
    area_is_in_ha = False
    data_access = """
    Data must be obtained from the Varda API, saved as .json files. Easiest way to try it out is
    to use the UI at https://fieldid.varda.ag/ and find some fields and click 'download .json' file,
    or else call the /boundaries endpoint - details at https://developer.varda.ag/reference/get_boundaries_by_spatial_field_relationship_search-1.
    Use the `-i` option to provide the file(s) to the converter.
    """

    id = "varda"
    short_name = "Varda"
    title = "Varda Global FieldID"
    description = """Field Boundaries from the Global FieldID system from Varda."""

    provider = "Varda <https://www.varda.ag>"
    attribution = "© 2024 Varda"
    license = "Varda Terms of use <https://fieldid.varda.ag/help/terms-conditions>"

    columns = {
        "geometry": "geometry",
        "id": "id",
        "area": "metrics:area",
        "perimeter": "metrics:perimeter",
        # todo: add more columns?
        # "effective_from": "datetime:valid_from",
        # "effective_until": "datetime:valid_until",
        # 0000-01-01T00:00:00.000Z and 9999-12-31T00:00:00.000Z should be converted to None
    }
