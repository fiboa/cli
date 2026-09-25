import geopandas as gpd
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin


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
    provider = "Bayerische Vermessungsverwaltung <https://www.ldbv.bayern.de>"
    mapping_file = "https://fiboa.org/code/de/de_by.csv"
    hcat_mapping_csv = "https://fiboa.org/code/de/de_by.csv"

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
        names = self.hcat_lookup("original_code", "original_name")
        gdf = gdf[gdf["bewirtschaftung"].isin(names)]
        gdf["crop:name"] = gdf["bewirtschaftung"].map(names)
        return gdf
