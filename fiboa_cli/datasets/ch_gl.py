from .ch_base import SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch_gl"
    canton = "GL"
    short_name = "Switzerland, Glarus"
    title = "Field boundaries for the canton of Glarus, Switzerland"
    description = "The agricultural usage areas (Nutzungsflächen) of the canton of Glarus, in their current state on geodienste.ch."
    provider = f"Kanton Glarus, via geodienste.ch <{SERVICE_PAGE}>"
    license = "opendata.swiss terms: Open use; Kanton Glarus OGD Nutzungsbestimmungen <https://www.geodienste.ch/pdfs/GL/lwb_nutzungsflaechen/data/ktgl-ogd-geo-20260622.pdf>"
    attribution = f"Kanton Glarus — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"
