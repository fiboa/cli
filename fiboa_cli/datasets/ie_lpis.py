from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin

BASE = "https://opendata.agriculture.gov.ie/dataset"
# data.gov.ie dataset, parcels resource and file per campaign; 2023 and 2024 were never published
EDITIONS = {
    "2025": (
        "40d859ac-58a8-4082-98d2-4ebf1c7cdd29",
        "bd5a8a3b-cc9f-498d-9f40-dc7006d4efee",
        "geo_860-parcels_gpk_2025.zip",
    ),
    "2022": (
        "ecd6db57-820f-48c0-8142-5aaae7378689",
        "8797641f-2f58-4f3b-a5e3-8427de8c9bea",
        "geoserviceshelp-100_parcels_rnd_2022.zip",
    ),
    "2021": (
        "1a87e9f7-a6a0-4f0f-845d-1b1ce6babd6d",
        "3f358eba-17ab-4ea9-a8e8-c9e4ce56cf50",
        "geoserviceshelp-54_parcels_2021_enc.zip",
    ),
    "2020": (
        "ccac60d7-bc9b-40ec-83ba-198904d759f6",
        "11b02a59-6885-47f9-9b5c-6af33f0feed5",
        "geoserviceshelp-54_parcels_2020_enc.zip",
    ),
    "2019": (
        "e70b1882-8b87-4e29-940c-bd7d84110a09",
        "843134db-cc82-4d7a-ac4f-d3a7a1b96146",
        "geoserviceshelp-54_parcels_2019_enc.zip",
    ),
    "2018": (
        "dc7a6e57-673f-45ea-96fd-d30d1c8160ae",
        "c19b3135-2dd6-493d-816d-eed6584e3cc3",
        "geoserviceshelp-54_parcels_2018_enc.zip",
    ),
    "2017": (
        "a2e8ac1d-0776-4f6d-93f4-ffbf111117f0",
        "63eb5ec0-e643-4d42-84d6-fe27e362cfac",
        "geoserviceshelp-54_parcels_2017_enc.zip",
    ),
}
# The 2025 GeoPackage renamed the fields; the shapefiles truncate the dictionary's names to 10 characters
FIELDS = {
    "par_lab": "PARC_LAB",
    "crop": "CROP_DESC",
    "digitised": "DIGIT_AREA",
    "eh_area": "MEA",
    "claim_area": "CLAIM_AREA",
    "commonage_ind": "COM_IND",
}


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    # The shapefile zips are read as they are (two shapefiles each, the first at the DBF size limit);
    # the 2025 GeoPackage is extracted, SQLite does not work through a zip
    variants = {
        year: {
            f"{BASE}/{dataset}/resource/{resource}/download/{file}": (
                ["*.gpkg"] if year == "2025" else file
            )
        }
        for year, (dataset, resource, file) in EDITIONS.items()
    }
    id = "ie_lpis"
    short_name = "Ireland (LPIS)"
    title = "LPIS parcels for Ireland"
    description = """
Every parcel of Ireland's LPIS with the crop declared on it, from the "Anonymous LPIS" datasets the
Department of Agriculture, Food and the Marine publishes per campaign year (none for 2023 and 2024).
The source has one row per claim; here a parcel is one row with the crop of its largest claim, its
digitised and eligible area and the area claimed by all applicants together. Unclaimed parcels
(buildings, farmyards, bog) are kept and parcel identifiers are hashed by the department.
    """
    provider = "Department of Agriculture, Food and the Marine <https://data.gov.ie/organization/department-of-agriculture-food-and-the-marine>"
    attribution = "Ireland Department of Agriculture, Food and the Marine"
    license = "CC-BY-4.0"
    ec_mapping_csv = (
        "https://fiboa.org/code/ie/ie.csv"  # the GSAA list, extended by the LPIS-only names
    )
    area_is_in_ha = False
    columns = {
        "geometry": "geometry",
        "PARC_LAB": "id",
        "CROP_DESC": "crop:name",
        "crop:code": "crop:code",  # the name, the source has no code
        "DIGIT_AREA": "metrics:area",
        "MEA": "eligible_area",
        "CLAIM_AREA": "claimed_area",
        "COM_IND": "commonage",
    }
    column_migrations = {
        "DIGIT_AREA": lambda col: col.astype(float) * 10_000,  # float32 in the GeoPackage
        "COM_IND": lambda col: col == "Y",
    }
    missing_schemas = {
        "properties": {
            "eligible_area": {"type": "double"},  # maximum eligible area, hectares
            "claimed_area": {"type": "double"},  # claimed by all applicants together, hectares
            "commonage": {"type": "boolean"},
        }
    }

    def read_data(self, paths, **kwargs):
        if self.variant == "2025":
            # 3.4 million rows carry no attribute at all: unclaimed slivers, median 20 m²
            kwargs.update(columns=list(FIELDS), where="crop IS NOT NULL")
        else:
            kwargs["columns"] = list(FIELDS.values())
        return super().read_data(paths, **kwargs)

    def file_migration(self, gdf, path, uri, layer=None):
        return gdf.rename(columns=FIELDS)

    def migrate(self, gdf):
        # A row is a claim and carries the parcel's geometry: commonage and partnerships repeat a
        # parcel per applicant, a parcel split into crops per crop. Keep one row per parcel with
        # the crop of the largest claim and the claims added up.
        gdf = gdf.sort_values(
            ["PARC_LAB", "CLAIM_AREA", "CROP_DESC"], ascending=[True, False, True]
        )
        gdf["CLAIM_AREA"] = gdf.groupby("PARC_LAB")["CLAIM_AREA"].transform("sum")
        gdf = gdf.drop_duplicates("PARC_LAB")
        gdf["crop:code"] = gdf["CROP_DESC"]
        return super().migrate(gdf)
