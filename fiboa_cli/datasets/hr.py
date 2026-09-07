from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin

base = "https://www.apprrr.hr/wp-content/uploads/nipp"


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    variants = {
        "2024": f"{base}/land_parcels.gpkg",
        **{str(y): f"{base}/arkod_31_12_{y}.gpkg" for y in range(2023, 2010, -1)},
    }
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
        # Nothing here is required. The editions carry different subsets — the
        # 2011 archive has 17 of these columns, 2023 has 25, jpaid appears only
        # in the current one — and the columns that do exist are often empty:
        # 2011 leaves mines_status null for 909k of its 1.29M parcels and
        # water_protect_zone and natura2000 null for 1.00M.
        "required": [],
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
    use_variant_as_determination = True

    # The current edition declares HTRS96 / Croatia TM; the archives leave
    # gpkg_geometry_columns.srs_id at 0 ("Undefined geographic SRS") although
    # their coordinates are the same projected metres — 264979..731547 E maps
    # onto Croatia from EPSG:3765 and nowhere else.
    ARCHIVE_CRS = "EPSG:3765"

    def migrate(self, gdf):
        if gdf.crs is None or gdf.crs.to_epsg() is None:
            # Left undeclared, the bogus geographic CRS reaches the STAC extent as
            # projected metres, and the Hilbert grid spans the whole globe while
            # the data sits in one cell of it.
            gdf = gdf.set_crs(self.ARCHIVE_CRS, allow_override=True)

        # The dated archives carry ARKOD's own parcel id, unique per edition and
        # stable enough to follow a parcel across years — the reason to prefer it
        # over a row number. The rolling land_parcels.gpkg ships no identifier at
        # all, so there the row index is all there is.
        if "id" not in gdf.columns:
            gdf["id"] = gdf.index
        return super().migrate(gdf)
