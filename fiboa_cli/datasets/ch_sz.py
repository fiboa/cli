from ..conversion.converter_wfs import WFSConverterMixin
from .ch_base import CHBaseConverter


class Converter(WFSConverterMixin, CHBaseConverter):
    canton = "SZ"
    # 2025 is the geodienste.ch file (None), the earlier years the canton's own WFS layers
    variants = {"2025": None, "2024": "2024", "2023": "2023", "2022": "2022"}
    description = """
The agricultural usage areas (Nutzungsflächen) of the canton of Schwyz: the current year from
the canton's file on geodienste.ch, 2022 to 2024 from the canton's own WFS, whose layers keep
one feature per part of a field and few attributes, so the area is measured and the ids differ
from the current year's.
    """
    provider = "Kanton Schwyz, Amt für Landwirtschaft <https://www.sz.ch/landwirtschaft>"

    wfs_url = "https://map.geo.sz.ch/mapserv_proxy"
    wfs_page_size = 20_000  # GML 3.2 is the only output; a page of 20k features is 45 MB
    # a multipart field is one feature per part with the same id: the base numbers the parts, and
    # groesse (the whole field, in ares) is left out so each part is measured
    source_columns = {
        "nutzungsid": "nutzungsidentifikator",
        "nutzart_co": "lnf_code",
        "nutzart": "nutzung",
    }

    def get_wfs_params(self):
        # MapServer pages in a stable order only when sorted
        return {"typeNames": f"ms:ch.sz.a002a.nutzung.{self.variant}", "sortBy": "nutzungsid"}

    def get_urls(self):
        if self.variants[self.variant] is None:
            return CHBaseConverter.get_urls(self)  # the geodienste.ch file
        return super().get_urls()  # the WFS pages
