import geopandas as gpd
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin, load_ec_mapping


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    sources = "https://geodaten.bayern.de/odd/m/3/daten/ln/landnutzung.gpkg"
    avoid_range_request = True

    id = "de_by"
    admin_subdivision_code = "BY"
    short_name = "Germany, Bavaria"
    title = "Field boundaries for Bavaria, Germany"
    description = """A field block (German: "Feldblock") is a contiguous agricultural area surrounded by permanent boundaries, which is cultivated by one or more farmers with one or more crops, is fully or partially set aside or is fully or partially taken out of production."""
    license = "CC-BY-4.0"
    attribution = "Datenquelle: Bayerische Vermessungsverwaltung – www.geodaten.bayern.de"
    providers = [
        {
            "name": "Bayerische Vermessungsverwaltung",
            "url": "https://www.ldbv.bayern.de",
            "roles": ["producer", "licensor"],
        }
    ]
    mapping_file = "https://fiboa.org/code/de/de_by.csv"
    ec_mapping_csv = "https://fiboa.org/code/de/de_by.csv"

    columns = {
        "geometry": "geometry",
        "uuid": "id",
        "datumderletztenueberpruefung": "determination:datetime",
        "bewirtschaftung": "crop:code",
        "crop:name": "crop:name",
    }

    def layer_filter(self, layer: str, uri: str) -> bool:
        return layer == "ln_landwirtschaft"

    def migrate(self, gdf: gpd.GeoDataFrame):
        gdf = super().migrate(gdf)
        self.ec_mapping = load_ec_mapping(self.ec_mapping_csv, url=self.mapping_file)
        gdf = gdf[gdf["bewirtschaftung"].isin([row["original_code"] for row in self.ec_mapping])]

        mapping_crop = {row["original_code"]: row["original_name"] for row in self.ec_mapping}
        gdf["crop:name"] = gdf["bewirtschaftung"].map(mapping_crop)
        return gdf
