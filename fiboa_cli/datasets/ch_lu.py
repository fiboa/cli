from .ch_base import SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch_lu"
    canton = "LU"
    short_name = "Switzerland, Luzern"
    title = "Field boundaries for the canton of Luzern, Switzerland"
    description = "The agricultural usage areas (Nutzungsflächen) of the canton of Luzern, in their current state on geodienste.ch."
    provider = f"Kanton Luzern, via geodienste.ch <{SERVICE_PAGE}>"
    license = "CC-BY-4.0"
    attribution = f"Kanton Luzern — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"
