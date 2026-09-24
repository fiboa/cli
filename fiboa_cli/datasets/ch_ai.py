from .ch_base import SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch_ai"
    canton = "AI"
    short_name = "Switzerland, Appenzell Innerrhoden"
    title = "Field boundaries for the canton of Appenzell Innerrhoden, Switzerland"
    description = "The agricultural usage areas (Nutzungsflächen) of the canton of Appenzell Innerrhoden, in their current state on geodienste.ch."
    provider = f"Kanton Appenzell Innerrhoden, via geodienste.ch <{SERVICE_PAGE}>"
    license = "CC-BY-4.0"
    attribution = f"Grundlage/Quelle: Geodaten Kanton/Bezirke Appenzell I.Rh. — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"
