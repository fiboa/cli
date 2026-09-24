from .ch_base import SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch_ag"
    canton = "AG"
    short_name = "Switzerland, Aargau"
    title = "Field boundaries for the canton of Aargau, Switzerland"
    description = "The agricultural usage areas (Nutzungsflächen) of the canton of Aargau, in their current state on geodienste.ch."
    provider = f"Kanton Aargau, via geodienste.ch <{SERVICE_PAGE}>"
    license = "opendata.swiss terms: Open use. Must provide the source; Kanton Aargau Nutzungsbedingungen <https://www.ag.ch/geoportal/geodatenshop/Nutzungsbedingungen.aspx?Typ=NutzungsbedingungenAGIS1>"
    attribution = f"Daten des Kantons Aargau — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"
