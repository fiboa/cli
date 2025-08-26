import numpy as np
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.data import read_data_csv
from .commons.ec import ec_url


class Converter(AdminConverterMixin, FiboaBaseConverter):
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

    providers = [
        {
            "name": "Agencija za plaćanja u poljoprivredi, ribarstvu i ruralnom razvoju",
            "url": "https://www.apprrr.hr/prostorni-podaci-servisi/",
            "roles": ["producer", "licensor"],
        }
    ]

    attribution = (
        "copyright © 2024. Agencija za plaćanja u poljoprivredi, ribarstvu i ruralnom razvoju"
    )

    license = {
        "title": "Prostorni podaci i servisi",
        "href": "https://www.apprrr.hr/prostorni-podaci-servisi/",
        "type": "text/html",
        "rel": "license",
    }
    index_as_id = True

    columns = {
        "id": "id",
        "land_use_id": "crop:code",
        "crop:name": "crop:name",
        "crop:name_en": "crop:name_en",
        "area": "metrics:area",
        "geometry": "geometry",
        "home_name": "home_name",
        "perim": "metrics:perimeter",
        "slope": "slope",
        "z_avg": "z_avg",
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

    extensions = {"https://fiboa.github.io/crop-extension/v0.2.0/schema.yaml"}
    column_additions = {"crop:code_list": ec_url("hr_2020.csv")}

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
            "land_use_id": {"type": "double"},
            "home_name": {"type": "string"},
            "slope": {"type": "double"},
            "z_avg": {"type": "double"},
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

    def migrate(self, gdf):
        gdf = super().migrate(gdf)
        rows = read_data_csv("hr_categories.csv", delimiter=";")
        mapping = {int(row["code"]): row["name"] for row in rows}
        mapping_en = {int(row["code"]): row["name_en"] for row in rows}
        gdf["crop:name"] = gdf["land_use_id"].map(mapping)
        gdf["crop:name_en"] = gdf["land_use_id"].map(mapping_en)
        gdf["area"] = np.where(gdf["area"] == 0, gdf["geometry"].area / 10000, gdf["area"] / 10000)
        return gdf
