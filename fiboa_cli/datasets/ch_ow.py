from .ch_base import SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch_ow"
    canton = "OW"
    short_name = "Switzerland, Obwalden"
    title = "Field boundaries for the canton of Obwalden, Switzerland"
    description = "The agricultural usage areas (Nutzungsflächen) of the canton of Obwalden, in their current state on geodienste.ch."
    provider = f"Kanton Obwalden, via geodienste.ch <{SERVICE_PAGE}>"
    license = "GIS Daten AG Nutzungsbestimmungen für Geodaten und Geodienste (approval required) <https://www.gis-daten.ch/downloads/public/Richtlinien_Weisungen/Nutzungsbestimmungen_Geodaten_und_Geodienste.pdf>"
    attribution = f"Quelle: GIS Daten AG, Kanton Obwalden — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"
    data_access = (
        "The canton has to approve the download on geodienste.ch: apply at "
        f"{SERVICE_PAGE}, export the GeoPackage and convert it with "
        "`fiboa convert ch_ow -i <zip>|geopackage/*.gpkg`."
    )
