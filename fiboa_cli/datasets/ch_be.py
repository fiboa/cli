from .ch_base import SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch_be"
    canton = "BE"
    short_name = "Switzerland, Bern"
    title = "Field boundaries for the canton of Bern, Switzerland"
    description = "The agricultural usage areas (Nutzungsflächen) of the canton of Bern, in their current state on geodienste.ch."
    provider = f"Kanton Bern, via geodienste.ch <{SERVICE_PAGE}>"
    license = "opendata.swiss terms: Open use. Must provide the source; Kanton Bern geoproduct LANDKULT <https://www.agi.dij.be.ch/de/start/geoportal/geodaten/detail.html?type=geoproduct&code=LANDKULT>"
    attribution = (
        f"Kanton Bern, Amt für Geoinformation — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"
    )
