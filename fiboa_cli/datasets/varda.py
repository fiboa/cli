# Converter for Varda field boundary datasets to Fiboa.
# Aiming to have it work with both direct API access and with bulk download.

from ..conversion.fiboa_converter import FiboaBaseConverter

# According to the Varda API the following values seem to be the only allowed values at this moment.
# We keep the converter flexible though to allow for future changes.
AREA_CONVERSION_FACTORS = {  # target unit: hectares
    "m2": 1 / 10000,  # 1 square meter = 0.0001 hectares
}
LENGTH_CONVERSION_FACTORS = {  # target unit: meters
    "m": 1,
}


def convert_from_unit(row, prefix, conversion_factors):
    value = row[f"{prefix}.value"]
    unit = row[f"{prefix}.unit"]
    factor = conversion_factors.get(unit)
    if factor is not None:
        return value * conversion_factors[unit]
    else:
        raise ValueError(f"Unknown unit '{unit}' in column '{prefix}.unit'")


class Converter(FiboaBaseConverter):
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

    providers = [{"name": "Varda", "url": "https://www.varda.ag/", "roles": ["licensor"]}]
    attribution = "© 2024 Varda"
    license = {
        "title": "Varda Terms of use",
        "href": "https://fieldid.varda.ag/help/terms-conditions",
        "type": "text/html",
        "rel": "license",
    }

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

    # EXTENSIONS = {
    #    "https://fiboa.github.io/timestamps-extension/v0.1.0/schema.yaml"
    # }

    def migrate(self, gdf):
        gdf["area"] = gdf.apply(
            lambda row: convert_from_unit(row, "area", AREA_CONVERSION_FACTORS), axis=1
        )
        gdf["perimeter"] = gdf.apply(
            lambda row: convert_from_unit(row, "perimeter", LENGTH_CONVERSION_FACTORS), axis=1
        )
        return gdf
