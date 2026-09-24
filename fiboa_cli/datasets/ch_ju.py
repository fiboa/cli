from .ch_base import SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch_ju"
    canton = "JU"
    short_name = "Switzerland, Jura"
    title = "Field boundaries for the canton of Jura, Switzerland"
    description = "The agricultural usage areas (Nutzungsflächen) of the canton of Jura, in their current state on geodienste.ch."
    provider = f"Kanton Jura, via geodienste.ch <{SERVICE_PAGE}>"
    license = "CC-BY-4.0"
    attribution = f"Géodonnées de la République et Canton du Jura — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"
