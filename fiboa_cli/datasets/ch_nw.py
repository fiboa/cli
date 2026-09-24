from .ch_base import SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch_nw"
    canton = "NW"
    short_name = "Switzerland, Nidwalden"
    title = "Field boundaries for the canton of Nidwalden, Switzerland"
    description = "The agricultural usage areas (Nutzungsflächen) of the canton of Nidwalden, in their current state on geodienste.ch."
    provider = f"Kanton Nidwalden, via geodienste.ch <{SERVICE_PAGE}>"
    license = "GIS Daten AG Nutzungsbestimmungen für Geodaten und Geodienste (approval required) <https://www.gis-daten.ch/downloads/public/Richtlinien_Weisungen/Nutzungsbestimmungen_Geodaten_und_Geodienste.pdf>"
    attribution = f"Quelle: GIS Daten AG, Kanton Nidwalden — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"
    data_access = (
        "The canton has to approve the download on geodienste.ch: apply at "
        f"{SERVICE_PAGE}, export the GeoPackage and convert it with "
        "`fiboa convert ch_nw -i <zip>|geopackage/*.gpkg`."
    )
