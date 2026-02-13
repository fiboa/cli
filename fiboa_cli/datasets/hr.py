from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    sources = "https://www.apprrr.hr/wp-content/uploads/nipp/land_parcels.gpkg"
    id = "hr"
    short_name = "Croatia"
    title = "Croatian Field Boundaries"
    description = """
Field boundary data for Croatia, provided as part of national agricultural datasets.

This dataset contains spatial data related to agricultural land use in Croatia, including ARKOD parcel information,
environmentally sensitive areas, High Nature Value Grasslands, protective buffer strips around watercourses, and vineyard
classifications. The data is crucial for managing agricultural activities, ensuring compliance with environmental regulations,
and supporting sustainable land use practices.
    """

    provider = "Agencija za plaćanja u poljoprivredi, ribarstvu i ruralnom razvoju <https://www.apprrr.hr/prostorni-podaci-servisi/>"

    attribution = (
        "copyright © 2024. Agencija za plaćanja u poljoprivredi, ribarstvu i ruralnom razvoju"
    )

    license = "Prostorni podaci i servisi <https://www.apprrr.hr/prostorni-podaci-servisi/>"
    index_as_id = True

    column_migrations = {"land_use_id": lambda col: col.astype(int)}

    columns = {
        "id": "id",
        "land_use_id": "crop:code",
        "area": "metrics:area",
        "geometry": "geometry",
        "home_name": "home_name",
        "perim": "metrics:perimeter",
        "slope": "slope",
        "z_avg": "height",
        "eligibility_coef": "eligibility_coef",
        "mines_status": "mines_status",
        "mines_year_removed": "mines_year_removed",
        "water_protect_zone": "water_protect_zone",
        "natura2000": "natura2000",
        "natura2000_ok": "natura2000_ok",
        "natura2000_pop": "natura2000_pop",
        "natura2000_povs": "natura2000_povs",
        "anc": "anc",
        "anc_area": "anc_area",
        "rp": "rp",
        "sanitary_protection_zone": "sanitary_protection_zone",
        "tvpv": "tvpv",
        "ot_nat": "ot_nat",
        "ot_nat_area": "ot_nat_area",
        "irrigation": "irrigation",
        "irrigation_source": "irrigation_source",
        "irrigation_type": "irrigation_type",
        "jpaid": "jpaid",
    }

    ec_mapping_csv = "hr_2020.csv"

    missing_schemas = {
        "required": [
            "mines_status",
            "water_protect_zone",
            "natura2000",
            "sanitary_protection_zone",
            "irrigation",
            "jpaid",
        ],
        "properties": {
            "land_use_id": {"type": "integer"},
            "home_name": {"type": "string"},
            "slope": {"type": "double"},
            "height": {"type": "double"},
            "eligibility_coef": {"type": "double"},
            "mines_status": {"type": "string", "enum": ["N", "M", "R"]},
            "mines_year_removed": {"type": "int32"},
            "water_protect_zone": {"type": "string"},
            "natura2000": {"type": "double"},
            "natura2000_ok": {"type": "string"},
            "natura2000_pop": {"type": "double"},
            "natura2000_povs": {"type": "double"},
            "anc": {"type": "int32"},
            "anc_area": {"type": "double"},
            "rp": {"type": "int32"},
            "sanitary_protection_zone": {"type": "string"},
            "tvpv": {"type": "int32"},
            "ot_nat": {"type": "int32"},
            "ot_nat_area": {"type": "double"},
            "irrigation": {"type": "int32"},
            "irrigation_source": {"type": "int32"},
            "irrigation_type": {"type": "int32"},
            "jpaid": {"type": "string"},
        },
    }

    area_is_in_ha = False
    area_calculate_missing = True
