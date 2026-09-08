import geopandas as gpd
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
        # Marknr numbers a field within one application, so on its own it repeats
        # across holdings — 38 of 100 sampled 2026 rows shared one. From 2014 the
        # source names the application (Journalnr) and the pair identifies a
        # field; where the application is missing (70 of 599,008 rows in 2015,
        # the worst edition) the id is left empty and the row is dropped
        # downstream, rather than every such row sharing an id of "nan".
        #
        # The older editions name the applicant instead — Ansoeger until 2011,
        # KUNDE_LB in 2012 and 2013 — and that pair genuinely repeats: 5,124 keys
        # cover 11,534 of the 678,347 fields of 2008, mostly distinct polygons of
        # distinct size. Nothing there identifies a field, so the row index does,
        # which is safe because an edition is one file. Neither form carries
        # across editions: a new application number is issued every year.
        if "Journalnr" in gdf.columns:
            key = gdf["Journalnr"].astype(str) + ":" + gdf["Marknr"].astype(str)
            gdf["id"] = key.where(gdf["Journalnr"].notna() & gdf["Marknr"].notna())
        else:
            gdf["id"] = gdf.index

        if "Afgkode" in gdf.columns:
            gdf["Afgkode"] = gdf["Afgkode"].astype(float).fillna(value=0).astype(int).astype(str)
        # the 2008 and 2009 editions carry no crop columns (boundaries only)
        return super().migrate(gdf)
