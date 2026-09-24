from .ch_base import SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch_ai"
    canton = "AI"
    short_name = "Switzerland, Appenzell Innerrhoden"
    title = "Field boundaries for the canton of Appenzell Innerrhoden, Switzerland"
    description = "The agricultural usage areas (Nutzungsflächen) of the canton of Appenzell Innerrhoden, in their current state on geodienste.ch."
    provider = f"Kanton Appenzell Innerrhoden, via geodienste.ch <{SERVICE_PAGE}>"
    license = "opendata.swiss terms: Open use. Must provide the source; Kanton Appenzell Innerrhoden Nutzungsbedingungen <https://www.geodienste.ch/pdfs/AI/lwb_nutzungsflaechen/data/Nutzungsbedingungen_AI_annex-123-2.pdf>"
    attribution = f"Grundlage/Quelle: Geodaten Kanton/Bezirke Appenzell I.Rh. — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"
