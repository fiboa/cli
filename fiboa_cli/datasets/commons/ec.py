from typing import Sequence

from fiboa_cli.datasets.commons.hcat import AddHCATMixin


class EuroCropsConverterMixin(AddHCATMixin):
    """
    Adds HCAT columns to a GeoDataFrame, useful for transforming datasets supplied by the Eurocrops project.
    The Eurocrops files have their own column names, so we need to map them to HCAT extension names.
    Also modifies the dataset title and provider to reflect the source.
    """

    ec_year = None
    hcat_columns = {
        "EC_trans_n": "hcat:name_en",
        "EC_hcat_n": "hcat:name",
        "EC_hcat_c": "hcat:code",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.id.startswith("ec_"):
            self.id = "ec_" + self.id
        suffix = " - Eurocrops"
        if self.ec_year is not None:
            suffix = f"{suffix} {self.ec_year}"

        self.title += suffix
        self.short_name += suffix

        provider = "EuroCrops <https://github.com/maja601/EuroCrops>"
        self.provider = (f"{self.provider}, {provider}") if self.provider else provider
        self.license = "CC-BY-SA-4.0"


JRC_V2_BASE = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DRLL/EuroCropsV2/gpqtv202"


class EuroCropsV2Mixin:
    """
    Converts the editions of a national dataset that only the JRC's EuroCrops V2 still offers, so
    that they fit the national collection: they take its crop table, admin codes and crop columns.
    A subclass names the national converter, the NUTS code of the files and the years it supplies.
    """

    national = None
    nuts: str = ""
    years: Sequence[int] = ()
    # Codes of rows that are no field, e.g. buildings or landscape elements
    drop_codes: set[str] = set()
    # The national table is keyed on crop names, which the source codes otherwise (ee)
    code_from_name = False

    description = """
The editions the national source no longer offers, from EuroCrops V2: the Joint Research Centre's
harmonised archive of the Geo-Spatial Aid Application declarations, one GeoParquet per NUTS region
and year in EPSG:3035. The crop codes are the national ones, mapped to HCAT with the national table.
    """
    provider = (
        "Joint Research Centre, European Commission "
        "<https://data.jrc.ec.europa.eu/dataset/b9fb9e67-78a9-4327-9d59-39a928d812d3>"
    )
    attribution = "European Commission, Joint Research Centre — EuroCropsV2"
    license = "CC-BY-4.0"

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        national = cls.national
        cls.id = f"ec_{national.id}"
        cls.short_name = national.short_name
        cls.title = f"{national.title.strip()} — EuroCrops V2"
        cls.variants = {
            str(y): f"{JRC_V2_BASE}/{cls.nuts}_{y}.parquet" for y in sorted(cls.years, reverse=True)
        }
        for attr in (
            "hcat_mapping_csv",
            "hcat_mapping_supplements",
            "hcat_mapping_name_fallback",
            "admin_country_code",
            "admin_subdivision_code",
        ):
            if hasattr(national, attr):
                setattr(cls, attr, getattr(national, attr))

        cls.columns = {
            "geometry": "geometry",
            "cropfield": "id",
            "area_ha": "metrics:area",
            "original_code": "crop:code",
        }
        if "crop:name" in national.columns.values():
            cls.columns["original_name"] = "crop:name"
        if cls.drop_codes:
            cls.column_filters = {"original_code": lambda col: ~col.isin(cls.drop_codes)}

    def migrate(self, gdf):
        # es 2023 stores its codes as floats
        codes = gdf["original_code"].astype("string").str.replace(r"\.0$", "", regex=True)
        if self.code_from_name:
            names = self.hcat_lookup("original_name", "original_code", strip=True)
            codes = gdf["original_name"].str.strip().map(names)
        gdf["original_code"] = codes
        return super().migrate(gdf)
