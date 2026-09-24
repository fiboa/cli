from .ch_base import SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch_zg"
    canton = "ZG"
    short_name = "Switzerland, Zug"
    title = "Field boundaries for the canton of Zug, Switzerland"
    description = "The agricultural usage areas (Nutzungsflächen) of the canton of Zug, in their current state on geodienste.ch."
    provider = f"Kanton Zug, via geodienste.ch <{SERVICE_PAGE}>"
    license = "CC-BY-4.0"
    attribution = f"Quelle: GIS Kanton Zug — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"
