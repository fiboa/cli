from .ch_base import SERVICE_PAGE, CHBaseConverter


class Converter(CHBaseConverter):
    id = "ch_bl"
    canton = "BL"
    short_name = "Switzerland, Basel-Landschaft"
    title = "Field boundaries for the canton of Basel-Landschaft, Switzerland"
    description = "The agricultural usage areas (Nutzungsflächen) of the canton of Basel-Landschaft, in their current state on geodienste.ch."
    provider = f"Kanton Basel-Landschaft, via geodienste.ch <{SERVICE_PAGE}>"
    license = "opendata.swiss terms: Open use. Must provide the source; Kanton Basel-Landschaft Nutzung von Geodaten <https://www.baselland.ch/politik-und-behorden/direktionen/volkswirtschafts-und-gesundheitsdirektion/amt-fur-geoinformation/geoportal/geodaten/nutzung-von-geodaten>"
    attribution = f"Kanton Basel-Landschaft — Landwirtschaftliche Nutzungsflächen, {SERVICE_PAGE}"
