from .ch_base import SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch_sh"
    canton = "SH"
    short_name = "Switzerland, Schaffhausen"
    title = "Field boundaries for the canton of Schaffhausen, Switzerland"
    description = "The agricultural usage areas (Nutzungsflächen) of the canton of Schaffhausen, in their current state on geodienste.ch."
    provider = f"Kanton Schaffhausen, via geodienste.ch <{SERVICE_PAGE}>"
    license = "CC0-1.0"
    attribution = f"Kanton Schaffhausen — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"
