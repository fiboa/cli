from .commons.ecaas import EcaasConverter, drive_url


class Converter(EcaasConverter):
    # GEOFILES/ECAAS_KENYA_GEOJSON.zip in Pula's KENYA folder, linked from the project documentation
    sources = {
        drive_url("1z4ysK3Ezk7oDjf658pzMNcCDO06_Gk6S"): [
            "ECAAS_KENYA_GEOJSON/ecaas_geojson_kenya.geojson"
        ]
    }
    id = "ke_ecaas"
    short_name = "Kenya (ECAAS crop cuts)"
    title = "Crop-cut farm polygons with crop type and yield for Kenya (ECAAS Bird's-Eye)"
    hcat_mapping_csv = "https://fiboa.org/code/ke/ecaas/crop.csv"
