from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    variants = {
        str(year): {
            f"https://rkg.gov.si/razno/portal_analysis/KMRS_{year}.rar": [f"**/KMRS_{year}.shp"]
        }
        for year in range(2024, 2018, -1)
    }
    id = "si"
    short_name = "Slovenia"
    title = "Slovenia Crop Fields"
    description = """
The Slovenian government provides slightly different, relevant open data sets called GERK, KMRS, RABA and EKRZ.
This converter uses the KRMS dataset, which includes CAP applications of the last year and discerns
around 150 different crop categories.
    """
    provider = "Ministry of Agriculture, Forestry and Food (Ministrstvo za kmetijstvo, gozdarstvo in prehrano) <https://www.gov.si/drzavni-organi/ministrstva/ministrstvo-za-kmetijstvo-gozdarstvo-in-prehrano/>"

    license = "Javno dostopni podatki: Publicly available data <https://rkg.gov.si/vstop/>"

    SLOVENE_GRID = "EPSG:3794"

    def migrate(self, gdf):
        if gdf.crs is None:
            gdf = gdf.set_crs(self.SLOVENE_GRID)
        return super().migrate(gdf)

    columns = {
        "geometry": "geometry",
        "ID": "id",
        "POLJINA_ID": "id",
        "GERK_PID": "block_id",
        "AREA": "metrics:area",
        "SIFRA_KMRS": "crop:code",
        "RASTLINA": "crop:name",
        "CROP_LAT_E": "crop:name_en",
        "CROP_LATIN": "crop:name_en",
    }
    ec_mapping_csv = "https://fiboa.org/code/si/si.csv"
    column_migrations = {
        "geometry": lambda col: col.make_valid(),
        "SIFRA_KMRS": lambda col: col.astype(str).str.strip().str.zfill(3),
    }
    area_is_in_ha = False
    area_calculate_missing = True
    missing_schemas = {
        "properties": {
            "block_id": {"type": "uint64"},
        }
    }
