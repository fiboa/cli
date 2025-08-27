from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter


class Converter(AdminConverterMixin, FiboaBaseConverter):
    sources = (
        "https://service.pdok.nl/rvo/referentiepercelen/atom/downloads/referentiepercelen.gpkg"
    )

    id = "nl"
    short_name = "Netherlands"
    title = "Field boundaries for The Netherlands"
    description = """
    A field block (Dutch: "Referentieperceel"), formerly known as "AAN" (Agrarisch Areaal Nederland),
    is a contiguous agricultural area surrounded by permanent boundaries, which is cultivated by one or
    more farmers with one or more crops, is fully or partially set aside or is fully or partially
    taken out of production.

    The following field block types exist:

    - Woods (Hout)
    - Agricultural area (Landbouwgrond)
    - Other (Overig)
    - Water (Water)

    We filter on "Agricultural area" in this converter.
    For crop data, look at BasisRegistratie gewasPercelen (BRP)
    """

    providers = [
        {
            "name": "RVO / PDOK",
            "url": "https://www.pdok.nl/introductie/-/article/referentiepercelen",
            "roles": ["producer", "licensor"],
        }
    ]
    # Both http://creativecommons.org/publicdomain/zero/1.0/deed.nl and http://creativecommons.org/publicdomain/mark/1.0/
    license = "CC0-1.0"
    column_additions = {"determination:datetime": "2023-06-15T00:00:00Z"}
    columns = {"geometry": "geometry", "id": "id", "area": "metrics:area", "versiebron": "source"}
    column_filters = {
        # type = "Hout" | "Landbouwgrond" | "Overig" | "Water"
        "type": lambda col: col == "Landbouwgrond"
    }
    index_as_id = True
    area_calculate_missing = True
    missing_schemas = {
        "properties": {
            "source": {"type": "string"},
        }
    }
