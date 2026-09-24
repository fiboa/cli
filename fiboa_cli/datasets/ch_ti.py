from .ch_base import SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch_ti"
    canton = "TI"
    short_name = "Switzerland, Ticino"
    title = "Field boundaries for the canton of Ticino, Switzerland"
    description = "The agricultural usage areas (Nutzungsflächen) of the canton of Ticino, in their current state on geodienste.ch."
    provider = f"Kanton Ticino, via geodienste.ch <{SERVICE_PAGE}>"
    license = "opendata.swiss terms: Open use. Must provide the source; Geoportale Ticino condizioni di utilizzo (registration required) <https://www4.ti.ch/dt/sg/sai/ugeo/temi/geoportale-ticino/geoportale/condizioni-utilizzo/>"
    attribution = f"Fonte: Amministrazione cantonale - Canton Ticino — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"
    data_access = (
        "Registration on geodienste.ch is required for this canton: apply at "
        f"{SERVICE_PAGE}, export the GeoPackage and convert it with "
        "`fiboa convert ch_ti -i <zip>|geopackage/*.gpkg`."
    )
