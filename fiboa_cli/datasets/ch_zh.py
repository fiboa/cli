from urllib.parse import urlencode

from .ch_base import CHBaseConverter

WFS = "https://maps.zh.ch/wfs/OGDZHWFS"
# The whole year comes in one request: 146k features are a 60 MB shapefile zip.
PARAMS = {
    "SERVICE": "WFS",
    "VERSION": "2.0.0",
    "REQUEST": "GetFeature",
    "COUNT": 200_000,
    "OUTPUTFORMAT": "application/shapefile",
}


def layer_url(year):
    layer = f"ms:ogd-0170_giszhpub_lw_nutzungsflaechen_{year}_f"
    return f"{WFS}?{urlencode({**PARAMS, 'TYPENAMES': layer})}"


class Converter(CHBaseConverter):
    id = "ch_zh"
    canton = "ZH"
    variants = {str(year): {layer_url(year): f"ch_zh_{year}.zip"} for year in range(2025, 2016, -1)}
    short_name = "Switzerland, Zürich"
    title = "Field boundaries for the canton of Zürich, Switzerland"
    description = """
The agricultural usage areas (Nutzungsflächen) of the canton of Zürich from the canton's own
open-data WFS, which keeps one layer per year since 2017. 2017 and 2018 cover only part of the
canton, as the digital recording was introduced step by step. The layers also hold the fields
that Zürich farms cultivate in neighbouring cantons (two per cent of the rows), as the canton's
file on geodienste.ch does.
    """
    provider = "Kanton Zürich, Amt für Landschaft und Natur <https://www.zh.ch/de/umwelt-tiere/landwirtschaft.html>"
    license = "CC0-1.0"
    attribution = "Kanton Zürich, Amt für Landschaft und Natur — Landwirtschaftliche Kulturflächen, https://maps.zh.ch/wfs/OGDZHWFS"

    def file_migration(self, gdf, path, uri, layer=None):
        # the canton's own names; the code is zero-padded and the area is in ares
        gdf = gdf.rename(
            columns={"gis_nr": "nutzungsidentifikator", "blw_nr": "lnf_code", "blw_name": "nutzung"}
        )
        gdf["lnf_code"] = gdf["lnf_code"].str.lstrip("0")
        gdf["flaeche_m2"] = gdf["flaeche"] * 100
        gdf["kanton"] = self.canton
        gdf["bezugsjahr"] = int(self.variant)
        gdf["ist_ueberlagernd"] = False  # the layers carry no overlapping elements
        return gdf
