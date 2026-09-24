from .ch_base import SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch_so"
    canton = "SO"
    short_name = "Switzerland, Solothurn"
    title = "Field boundaries for the canton of Solothurn, Switzerland"
    description = "The agricultural usage areas (Nutzungsflächen) of the canton of Solothurn, in their current state on geodienste.ch."
    provider = f"Kanton Solothurn, via geodienste.ch <{SERVICE_PAGE}>"
    license = "CC0-1.0"
    attribution = f"Kanton Solothurn — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"
