from .ch_base import SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch_gr"
    canton = "GR"
    short_name = "Switzerland, Graubünden"
    title = "Field boundaries for the canton of Graubünden, Switzerland"
    description = "The agricultural usage areas (Nutzungsflächen) of the canton of Graubünden, in their current state on geodienste.ch."
    provider = f"Kanton Graubünden, via geodienste.ch <{SERVICE_PAGE}>"
    license = "Nutzungsbestimmungen für Geodaten <https://geo.gr.ch/geodaten/nutzungsbedingungen>"
    attribution = f"Quelle: Landwirtschaftliche Nutzungsflächen, Kanton Graubünden — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"
