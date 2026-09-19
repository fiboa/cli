from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import EuroCropsConverterMixin


class Converter(EuroCropsConverterMixin, FiboaBaseConverter):
    ec_mapping_csv = "fr_2018.csv"
    ec_year = 2018
    sources = {
        "https://zenodo.org/records/14094196/files/FR_2018.zip": ["FR_2018/FR_2018_EC21.shp"]
    }

    id = "ec_fr"
    short_name = "France"
    title = "Field boundaries for France"
    description = """
The 2018 campaign of the Registre Parcellaire Graphique, which IGN never released as an
archive of its own: the RPG downloads run 2017 and 2019 onwards. EuroCrops publishes it
with its HCAT columns already resolved.
    """
    provider = "Institut National de l'Information Géographique et Forestière <https://geoservices.ign.fr/rpg>"
    attribution = "IGN - Original data from https://geoservices.ign.fr/rpg"

    columns = {
        "geometry": "geometry",
        "ID_PARCEL": "id",
        "SURF_PARC": "metrics:area",
        "CODE_CULTU": "crop:code",
        "CODE_GROUP": "group_code",
    }
    missing_schemas = {"properties": {"group_code": {"type": "string"}}}
    column_migrations = {
        "CODE_GROUP": lambda col: col.astype("string").str.strip(),
    }

    def migrate(self, gdf):
        # nine parcels are multi-part; splitting here rather than in the base converter
        # is what makes it possible to keep their parts apart in the id
        gdf = self.split_multipart(gdf)
        gdf["ID_PARCEL"] = gdf["ID_PARCEL"].astype("string")
        part = gdf.groupby("ID_PARCEL").cumcount()
        gdf.loc[part > 0, "ID_PARCEL"] += "-" + (part[part > 0] + 1).astype(str)

        # SURF_PARC is rounded to 0.01 ha, so a parcel under 50 m2 reads as zero
        zero = gdf["SURF_PARC"] <= 0
        if zero.any():
            self.info(f"Computing the area of {zero.sum():,} parcel(s) rounded down to zero")
            gdf.loc[zero, "SURF_PARC"] = gdf.loc[zero, "geometry"].area / 10_000
        return super().migrate(gdf)
