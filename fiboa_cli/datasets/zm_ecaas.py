from .commons.ecaas import EcaasConverter, drive_url


class Converter(EcaasConverter):
    # GEOFILES/ECAAS_ZAMBIA_GEOJSON.zip in Pula's ZAMBIA folder, linked from the project documentation
    sources = {
        drive_url("1kl7wnGYNCxn-ATdoB_yBwefoZ4AUAW-P"): [
            "ECAAS_ZAMBIA_GEOJSON/ecaas_zambia_geojson.geojson"
        ]
    }
    id = "zm_ecaas"
    short_name = "Zambia (ECAAS crop cuts)"
    title = "Crop-cut farm polygons with crop type and yield for Zambia (ECAAS Bird's-Eye)"
    hcat_mapping_csv = "https://fiboa.org/code/zm/ecaas/crop.csv"
