from urllib.parse import urlencode

from .ch_base import CHBaseConverter

WFS = "https://map.geo.sz.ch/mapserv_proxy"
# GML is the only output; the whole year comes in one request (32k features, 75 MB)
PARAMS = {"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature", "COUNT": 50_000}


def layer_url(year):
    return f"{WFS}?{urlencode({**PARAMS, 'TYPENAMES': f'ms:ch.sz.a002a.nutzung.{year}'})}"


class Converter(CHBaseConverter):
    id = "ch_sz"
    canton = "SZ"
    # 2025 is the canton's current file on geodienste.ch (None), the earlier years its own WFS layers
    variants = {"2025": None} | {
        str(year): {layer_url(year): f"ch_sz_{year}.gml"} for year in (2024, 2023, 2022)
    }
    short_name = "Switzerland, Schwyz"
    title = "Field boundaries for the canton of Schwyz, Switzerland"
    description = """
The agricultural usage areas (Nutzungsflächen) of the canton of Schwyz: the current year from
the canton's file on geodienste.ch, 2022 to 2024 from the canton's own WFS, whose layers keep
one feature per part of a field and few attributes, so the area is measured and the ids differ
from the current year's.
    """
    provider = "Kanton Schwyz, Amt für Landwirtschaft <https://www.sz.ch/landwirtschaft>"
    license = "CC-BY-4.0"
    attribution = "Amt für Landwirtschaft (AFL), Kanton Schwyz — Landwirtschaftliche Nutzungsflächen, https://www.geodienste.ch/services/lwb_nutzungsflaechen"

    def file_migration(self, gdf, path, uri, layer=None):
        if path.endswith(".gml"):
            # a multipart field is one feature per part with the same id; the base numbers
            # the repeats, and groesse (the whole field's area, in ares) is left out
            gdf = gdf.rename(
                columns={
                    "nutzungsid": "nutzungsidentifikator",
                    "nutzart_co": "lnf_code",
                    "nutzart": "nutzung",
                }
            )
            gdf["lnf_code"] = gdf["lnf_code"].astype(str).str.lstrip("0")
            gdf["kanton"] = self.canton
            gdf["bezugsjahr"] = int(self.variant)
            gdf["ist_ueberlagernd"] = False
        return gdf
