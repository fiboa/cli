from ..conversion.converter_wfs import WFSConverterMixin
from .ch_base import CHBaseConverter


class Converter(WFSConverterMixin, CHBaseConverter):
    canton = "ZH"
    # the canton's open-data WFS keeps one layer per year
    variants = {str(year): str(year) for year in range(2025, 2016, -1)}
    description = """
The agricultural usage areas (Nutzungsflächen) of the canton of Zürich from the canton's own
open-data WFS, which keeps one layer per year since 2017. 2017 and 2018 cover only part of the
canton, as the digital recording was introduced step by step. The layers also hold the fields
that Zürich farms cultivate in neighbouring cantons (two per cent of the rows), as the canton's
file on geodienste.ch does.
    """
    provider = "Kanton Zürich, Amt für Landschaft und Natur <https://www.zh.ch/de/umwelt-tiere/landwirtschaft.html>"
    attribution = "Kanton Zürich, Amt für Landschaft und Natur — Landwirtschaftliche Kulturflächen, https://maps.zh.ch/wfs/OGDZHWFS"

    wfs_url = "https://maps.zh.ch/wfs/OGDZHWFS"
    # One page per year (146k features, 64 MB of gzipped GML): the server has no maximum, and
    # MapServer pages in a stable order only when sorted, which a single page does not need. GML is
    # the server's own writer; its shapefile and GeoJSON writer fails now and then with a 400.
    wfs_page_size = 1_000_000
    # the canton's names; the code is zero-padded and the area is in ares
    source_columns = {
        "gis_nr": "nutzungsidentifikator",
        "blw_nr": "lnf_code",
        "blw_name": "nutzung",
        "flaeche": "flaeche_m2",
    }
    area_factor = 100

    def get_wfs_params(self):
        return {"typeNames": f"ms:ogd-0170_giszhpub_lw_nutzungsflaechen_{self.variant}_f"}
