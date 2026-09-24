from .ch_base import SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch_gl"
    canton = "GL"
    short_name = "Switzerland, Glarus"
    title = "Field boundaries for the canton of Glarus, Switzerland"
    description = "The agricultural usage areas (Nutzungsflächen) of the canton of Glarus, in their current state on geodienste.ch."
    provider = f"Kanton Glarus, via geodienste.ch <{SERVICE_PAGE}>"
    license = "CC0-1.0"
    attribution = f"Kanton Glarus — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"
