import geopandas as gpd
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.convert_gml import gml_assure_columns
from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.data import read_data_csv
from .commons.hcat import AddHCATMixin


class IEConverter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    variants = {
        str(year): {
            f"https://dafm-inspire-atom.s3.eu-west-1.amazonaws.com/files/LU/GSAA_{year}.zip": [
                f"GSAA_{year}.gml"
            ]
        }
        # the department's bucket answers for 2022 onwards; GSAA_2017 to
        # GSAA_2021 are gone (403, checked 2026-09-13)
        for year in range(2024, 2021, -1)
    }

    id = "ie"
    short_name = "Ireland"
    title = "Ireland INSPIRE Geospatial aid application (GSAA) dataset"
    description = "This data represents the outline shape of LPIS parcels as claimed under area based schemes. The dataset includes the crops claimed as part of the annual GSAA. Yearly information provided through the beneficiary declaration."

    provider = "Department of Agriculture, Food and the Marine <https://www.gov.ie/en/organisation/department-of-agriculture-food-and-the-marine/>"
    attribution = "Ireland Department of Agriculture, Food and the Marine"
    license = "CC-BY-4.0"
    columns = {
        "geometry": "geometry",
        "crop_name": "crop:name",
        "crop_code": "crop:code",
        "gml_id": "id",
        "localId": "parcel_id",
        "observationDate": "determination:datetime",
    }
    # localId is the LPIS parcel reference and repeats where a parcel is
    # declared more than once — 214 of the 1,027,438 rows of 2022, one of them
    # four times — so the feature id, which the GML guarantees unique, is the id.
    missing_schemas = {"properties": {"parcel_id": {"type": "string"}}}
    hcat_mapping_csv = "https://fiboa.org/code/ie/ie.csv"

    column_migrations = {
        "observationDate": lambda col: col.str.replace("+01:00", "T00:00:00Z"),
    }

    def migrate(self, gdf) -> gpd.GeoDataFrame:
        # crop_name can be multiple: "crop1, crop2, crop3". We only read the main crop (first).
        gdf["crop_name"] = gdf["crop_name"].str.split(", ").str.get(0)
        gdf = gdf[gdf["crop_name"] != "Void"]  # Exclude non-agriculture fields

        rows = read_data_csv("ie_2023.csv")
        mapping = {row["original_name"]: index + 1 for index, row in enumerate(rows)}
        gdf["crop_code"] = gdf["crop_name"].map(mapping)

        return super().migrate(gdf)

    def file_migration(
        self, gdf: gpd.GeoDataFrame, path: str, uri: str, layer: str = None
    ) -> gpd.GeoDataFrame:
        return gml_assure_columns(
            gdf,
            path,
            uri,
            layer,
            crop_name={"ElementPath": "specificLandUse@title", "Type": "String", "Width": 255},
        )

    def layer_filter(self, layer: str, uri: str) -> bool:
        return layer == "ExistingLandUseObject"
