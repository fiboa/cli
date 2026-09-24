from .ch_base import SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch_sg"
    canton = "SG"
    short_name = "Switzerland, St. Gallen"
    title = "Field boundaries for the canton of St. Gallen, Switzerland"
    description = "The agricultural usage areas (Nutzungsflächen) of the canton of St. Gallen, in their current state on geodienste.ch."
    provider = f"Kanton St. Gallen, via geodienste.ch <{SERVICE_PAGE}>"
    license = "Kanton St.Gallen Nutzungsbedingungen für Geodaten <https://www.sg.ch/bauen/geoinformation/datenbezug/agb.html>"
    attribution = f"Kanton St.Gallen — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"
