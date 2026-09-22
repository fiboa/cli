import geopandas as gpd
import pandas as pd
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin


class DKConverter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    variants = {
        str(variant): f"https://landbrugsgeodata.fvm.dk/Download/Marker/Marker_{variant}.zip"
        for variant in range(2026, 2008 - 1, -1)
    }
    id = "dk"
    short_name = "Denmark"
    title = "Denmark Crop Fields (Marker)"
    description = "The Danish Ministry of Food, Agriculture and Fisheries publishes Crop Fields (Marker) for each year."

    provider = "Danish Agricultural Agency <https://lbst.dk/>"
    ec_mapping_csv = "dk_2019.csv"
    # the codes that table has no row for, mapped from its own siblings
    ec_mapping_supplements = ["https://fiboa.org/code/dk/dk_supplement.csv"]
    # 2008 and 2009 publish no crop columns at all (no Afgkode, no Afgroede)
    variants_without_crops = {"2008", "2009"}
    license = "CC0-1.0"
    columns = {
        "geometry": "geometry",
        "id": "id",
        "IMK_areal": "metrics:area",
        "Afgkode": "crop:code",
        "Afgroede": "crop:name",
    }
    use_variant_as_determination = True

    def migrate(self, gdf) -> gpd.GeoDataFrame:
        # Marknr numbers a field within one application, so alone it repeats across
        # holdings. From 2014, Journalnr:Marknr identifies a field; rows missing
        # either part get a variant-scoped row number instead of all sharing "nan".
        if "Journalnr" in gdf.columns:
            key = gdf["Journalnr"].astype(str) + ":" + gdf["Marknr"].astype(str)
            fallback = f"{self.variant}:missing-application:" + gdf.index.astype(str)
            gdf["id"] = key.where(gdf["Journalnr"].notna() & gdf["Marknr"].notna(), fallback)
        else:
            # older editions carry no field identifier; the variant prefix keeps
            # row numbers unique across editions
            gdf["id"] = f"{self.variant}:" + gdf.index.astype(str)

        if "Afgkode" in gdf.columns:  # absent in the editions without crops
            # nullable int, so a missing code stays missing instead of becoming 0
            gdf["Afgkode"] = (
                pd.to_numeric(gdf["Afgkode"], errors="coerce").astype("Int64").astype("string")
            )
        return super().migrate(gdf)
