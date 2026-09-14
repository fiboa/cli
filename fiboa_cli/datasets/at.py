from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import AddHCATMixin


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    BASE = "https://inspire.lfrz.gv.at/009501/ds/"
    # Each archive holds a single GeoPackage; naming it makes vecorel extract the
    # zip once. Handing the archive itself to GDAL instead means re-inflating the
    # deflate stream on every SQLite seek: the 2018 edition read 85 GB out of a
    # 1.7 GB archive in 40 minutes and had still not finished reading the layer.
    variants = {
        "2025": {BASE + "inspire_schlaege_2025-1_polygon.gpkg.zip": ["*.gpkg"]},
        "2024": {BASE + "inspire_schlaege_2024-2_polygon.gpkg.zip": ["*.gpkg"]},
        "2023": {BASE + "inspire_schlaege_2023-2_polygon.gpkg.zip": ["*.gpkg"]},
        "2022": {BASE + "inspire_schlaege_2022_polygon.gpkg.zip": ["*.gpkg"]},
        "2021": {BASE + "inspire_schlaege_2021_polygon.gpkg.zip": ["*.gpkg"]},
        "2020": {BASE + "inspire_schlaege_2020_polygon.gpkg.zip": ["*.gpkg"]},
        "2019": {BASE + "inspire_schlaege_2019_polygon.gpkg.zip": ["*.gpkg"]},
        "2018": {BASE + "inspire_schlaege_2018_polygon.gpkg.zip": ["*.gpkg"]},
    }

    id = "at"
    country = "AT"
    short_name = "Austria"
    title = "Field boundaries for Austria"
    description = """
**Crop Field boundaries for Austria - INVEKOS Schläge Österreich 2025.**

This layer includes all field uses recorded by the applicants, which serve as the basis for the funding process. A field
is a contiguous area of a piece of land that is cultivated for a growing season with only one crop (field use type) and
uniform management requirements or as a landscape element type in accordance with Annex 1 of the regulation of the responsible
Federal Ministry with horizontal rules for the area of the Common Agricultural Policy (Horizontal CAP Regulation)
StF: BGBl. II No. 100/2015 or is simply maintained in good agricultural and ecological condition in accordance with
Art. 94 of Regulation (EU) No. 1306/2013 and is digitized in the GIS as a polygon or as a point.
    """
    provider = "Agrarmarkt Austria <https://geometadatensuche.inspire.gv.at/metadatensuche/inspire/api/records/9db8a0c3-e92a-4df4-9d55-8210e326a7ed>"
    license = "CC-BY-4.0"
    columns = {
        "GEO_ID": "id",
        "geometry": "geometry",
        "SNAR_CODE": "crop:code",
        "SNAR_BEZEICHNUNG": "crop:name",
        "SL_FLAECHE_BRUTTO_HA": "metrics:area",
        "GEOM_DATE_CREATED": "determination:datetime",
    }
    ec_mapping_csv = "https://fiboa.org/code/at/at.csv"
