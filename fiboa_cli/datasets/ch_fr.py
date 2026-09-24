from .ch_base import SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch_fr"
    canton = "FR"
    short_name = "Switzerland, Fribourg"
    title = "Field boundaries for the canton of Fribourg, Switzerland"
    description = "The agricultural usage areas (Nutzungsflächen) of the canton of Fribourg, in their current state on geodienste.ch."
    provider = f"Kanton Fribourg, via geodienste.ch <{SERVICE_PAGE}>"
    license = "opendata.swiss terms: Open use. Must provide the source <https://opendata.swiss/terms-of-use#terms_by>"
    attribution = (
        f"État de Fribourg / Kanton Freiburg — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"
    )
