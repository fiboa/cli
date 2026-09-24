from .ch_base import SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch_vs"
    canton = "VS"
    short_name = "Switzerland, Valais"
    title = "Field boundaries for the canton of Valais, Switzerland"
    description = "The agricultural usage areas (Nutzungsflächen) of the canton of Valais, in their current state on geodienste.ch."
    provider = f"Kanton Valais, via geodienste.ch <{SERVICE_PAGE}>"
    license = "opendata.swiss terms: Open use. Must provide the source <https://opendata.swiss/terms-of-use#terms_by>"
    attribution = (
        f"Canton du Valais / Kanton Wallis — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"
    )
