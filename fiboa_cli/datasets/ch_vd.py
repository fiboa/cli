from .ch_base import SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch_vd"
    canton = "VD"
    short_name = "Switzerland, Vaud"
    title = "Field boundaries for the canton of Vaud, Switzerland"
    description = "The agricultural usage areas (Nutzungsflächen) of the canton of Vaud, in their current state on geodienste.ch."
    provider = f"Kanton Vaud, via geodienste.ch <{SERVICE_PAGE}>"
    license = "Nutzungsbedingungen <https://www.vd.ch/territoire-et-construction/cadastre-et-geoinformation/geoservices/>"
    attribution = f"État de Vaud — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"
    data_access = (
        "The canton has to approve the download on geodienste.ch: apply at "
        f"{SERVICE_PAGE}, export the GeoPackage and convert it with "
        "`fiboa convert ch_vd -i <zip>|geopackage/*.gpkg`."
    )
