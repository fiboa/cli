from .ch_base import SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch_ne"
    canton = "NE"
    short_name = "Switzerland, Neuchâtel"
    title = "Field boundaries for the canton of Neuchâtel, Switzerland"
    description = "The agricultural usage areas (Nutzungsflächen) of the canton of Neuchâtel, in their current state on geodienste.ch."
    provider = f"Kanton Neuchâtel, via geodienste.ch <{SERVICE_PAGE}>"
    license = "opendata.swiss terms: Open use. Must provide the source; SITN conditions (registration required) <https://sitn.ne.ch/geoshop2_media/documents/contrat_sitn.pdf>"
    attribution = (
        f"Données SITN, http://www.ne.ch/sitn — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"
    )
    data_access = (
        "Registration on geodienste.ch is required for this canton: apply at "
        f"{SERVICE_PAGE}, export the GeoPackage and convert it with "
        "`fiboa convert ch_ne -i <zip>|geopackage/*.gpkg`."
    )
