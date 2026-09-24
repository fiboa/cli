from .ch_base import SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch_ju"
    canton = "JU"
    short_name = "Switzerland, Jura"
    title = "Field boundaries for the canton of Jura, Switzerland"
    description = "The agricultural usage areas (Nutzungsflächen) of the canton of Jura, in their current state on geodienste.ch."
    provider = f"Kanton Jura, via geodienste.ch <{SERVICE_PAGE}>"
    license = "opendata.swiss terms: Open use. Must provide the source; Canton du Jura conditions d'utilisation <https://geo.jura.ch/geodonnees/Conditions_utilisation_geodonnees.pdf>"
    attribution = f"Géodonnées de la République et Canton du Jura — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"
