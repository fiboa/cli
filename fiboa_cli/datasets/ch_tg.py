from .ch_base import SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch_tg"
    canton = "TG"
    short_name = "Switzerland, Thurgau"
    title = "Field boundaries for the canton of Thurgau, Switzerland"
    description = "The agricultural usage areas (Nutzungsflächen) of the canton of Thurgau, in their current state on geodienste.ch."
    provider = f"Kanton Thurgau, via geodienste.ch <{SERVICE_PAGE}>"
    license = "CC-BY-4.0"
    attribution = f"Kanton Thurgau — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"
