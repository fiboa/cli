import requests

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
    # One page per year (146k features, a 60 MB zip): the server has no maximum, its shapefile
    # writer fails with sortBy, and MapServer pages in a stable order only when sorted.
    wfs_page_size = 1_000_000
    wfs_extension = "zip"
    # the canton's names; the code is zero-padded and the area is in ares
    source_columns = {
        "gis_nr": "nutzungsidentifikator",
        "blw_nr": "lnf_code",
        "blw_name": "nutzung",
        "flaeche": "flaeche_m2",
    }
    area_factor = 100

    def get_wfs_params(self):
        return {
            "typeNames": f"ms:ogd-0170_giszhpub_lw_nutzungsflaechen_{self.variant}_f",
            "outputFormat": "application/shapefile",
        }

    @staticmethod
    def _download_file(source_fs, uri, cache_fs, cache_file):
        # the server answers fsspec's size probe (a ranged GET) with 400, so stream without it
        part_file = cache_file + ".part"
        try:
            with (
                requests.get(uri, stream=True, timeout=600) as response,
                cache_fs.open(part_file, mode="wb") as file,
            ):
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=10 * 1024 * 1024):
                    file.write(chunk)
        except BaseException:
            try:
                cache_fs.rm(part_file)
            except FileNotFoundError:
                pass
            raise
        cache_fs.mv(part_file, cache_file)
