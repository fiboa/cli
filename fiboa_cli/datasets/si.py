from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    variants = {
        str(year): {
            # 2019 nests the shapefile in a folder; the others keep it at the root
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

    # KMRS_2021.rar ships no .prj. Every other campaign declares EPSG:3794, and
    # 2021 covers the same extent (easting 377373..622579, as in 2020).
    SLOVENE_GRID = "EPSG:3794"

    def migrate(self, gdf):
        if gdf.crs is None:
            gdf = gdf.set_crs(self.SLOVENE_GRID)
        return super().migrate(gdf)

    # The campaigns disagree on names: 2019 calls the field POLJINA_ID and has
    # neither area nor crop name; 2020 spells the Latin name CROP_LATIN, later
    # campaigns CROP_LAT_E. Each edition carries one of each pair.
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
        # 2020 drops the leading zeros of the zero-padded KMRS codes, so
        # 120,164 of its 819,620 rows (14.66%) matched no crop.
        "SIFRA_KMRS": lambda col: col.astype(str).str.strip().str.zfill(3),
    }
    area_is_in_ha = False
    # 2019 publishes no area at all, so it is computed from the geometry
    area_calculate_missing = True
    missing_schemas = {
        "properties": {
            "block_id": {"type": "uint64"},
        }
    }
