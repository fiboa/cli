from .ch_base import SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch_ar"
    canton = "AR"
    short_name = "Switzerland, Appenzell Ausserrhoden"
    title = "Field boundaries for the canton of Appenzell Ausserrhoden, Switzerland"
    description = "The agricultural usage areas (Nutzungsflächen) of the canton of Appenzell Ausserrhoden, in their current state on geodienste.ch."
    provider = f"Kanton Appenzell Ausserrhoden, via geodienste.ch <{SERVICE_PAGE}>"
    license = "opendata.swiss terms: Open use; Kanton Appenzell Ausserrhoden Nutzungsbedingungen <https://ar.ch/fileadmin/user_upload/Departement_Bau_Volkswirtschaft/Amt_fuer_Raum_Wald/Geoinformation_und_Vermessung/AR_Nutzungsbedingungen_Geodaten.pdf>"
    attribution = (
        f"Kanton Appenzell Ausserrhoden — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"
    )
