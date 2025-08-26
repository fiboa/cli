from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter


class Converter(AdminConverterMixin, FiboaBaseConverter):
    sources = {
        "https://data.slovensko.sk/download?id=e39ad227-1899-4cff-b7c8-734f90aa0b59&blocksize=0": [
            "HU2024_20240917shp/HU2024_20240917.shp"
        ]
    }
    id = "sk"
    short_name = "Slovakia"
    title = "Slovakia Agricultural Land Identification System"
    description = """
    Systém identifikácie poľnohospodárskych pozemkov (LPIS)

    LPIS is an agricultural land identification system. It represents the vector boundaries of agricultural land
    and carries information about the unique code, acreage, culture/land use, etc., which is used as a reference
    for farmers' applications, for administrative and cross-checks, on-site checks and also checks using remote
    sensing methods.

    Dataset Hranice užívania contains the use declared by applicants for direct support.
    """
    providers = [
        {
            "name": "National catalog of open data",
            "url": "https://data.slovensko.sk/",
            "roles": ["producer", "licensor"],
        }
    ]
    license = "CC-0"  # "Open Data"
    # TODO look for a way to find codes for crop_name and implement crop-extension
    columns = {
        "geometry": "geometry",
        "KODKD": "id",
        "PLODINA": "crop_name",
        "KULTURA_NA": "crop_group",
        "LOKALITA_N": "municipality",
        "VYMERA": "metrics:area",
    }
    missing_schemas = {
        "properties": {
            "crop_name": {"type": "string"},
            "crop_group": {"type": "string"},
            "municipality": {"type": "string"},
        }
    }
