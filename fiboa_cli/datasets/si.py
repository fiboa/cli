from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    variants = {
        str(year): {
            # 2019 nests the shapefile in a KMRS_2019/ folder, the others keep it
            # at the root of the archive
            f"https://rkg.gov.si/razno/portal_analysis/KMRS_{year}.rar": [f"**/KMRS_{year}.shp"]
        }
        # rkg.gov.si keeps KMRS_<year>.rar for 2019 onwards; 2018 and 2025 are 404
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

    # KMRS_2021.rar ships the shapefile without a .prj, so its geometries arrive
    # naive and the conversion stops at the first transform. Every other campaign
    # declares EPSG:3794 (Slovenia 1996 / Slovene National Grid), and 2021 covers
    # the same ground in the same numbers: 377373..622579 easting against 2020's
    # 377373..622579.
    SLOVENE_GRID = "EPSG:3794"

    def migrate(self, gdf):
        if gdf.crs is None:
            gdf = gdf.set_crs(self.SLOVENE_GRID)
        return super().migrate(gdf)

    columns = {
        "geometry": "geometry",
        "ID": "id",
        "GERK_PID": "block_id",
        "AREA": "metrics:area",
        "SIFRA_KMRS": "crop:code",
        "RASTLINA": "crop:name",
        "CROP_LAT_E": "crop:name_en",
    }
    ec_mapping_csv = "https://fiboa.org/code/si/si.csv"
    column_migrations = {"geometry": lambda col: col.make_valid()}
    area_is_in_ha = False
    missing_schemas = {
        "properties": {
            "block_id": {"type": "uint64"},
        }
    }
