from .ch_base import SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch_ur"
    canton = "UR"
    short_name = "Switzerland, Uri"
    title = "Field boundaries for the canton of Uri, Switzerland"
    description = "The agricultural usage areas (Nutzungsflächen) of the canton of Uri, in their current state on geodienste.ch."
    provider = f"Kanton Uri, via geodienste.ch <{SERVICE_PAGE}>"
    license = "opendata.swiss terms: Open use. Must provide the source; GIS Uri Nutzungsbestimmungen <https://www.lisag.ch/nutzungsbestimmungen-gis-uri>"
    attribution = (
        f"Quelle: Lisag AG (GIS Uri) — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"
    )
