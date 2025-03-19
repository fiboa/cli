from fiboa_cli.datasets.commons.ec import ec_url
from fiboa_cli.datasets.commons.euro_land import EuroLandBaseConverter


class LTConverter(EuroLandBaseConverter):
    id = "lt"
    short_name = "Lithuania"
    title = "Lithuania crop fields"
    description = "Collection of data on agricultural land and crop areas, cultivated crops in the territory of the Republic of Lithuania"

    providers = [
        {
            "name": "Nacionalinė mokėjimo agentūra prie Žemės ūkio ministerijos",
            "url": "https://www.nma.lt/",
            "roles": ["producer", "licensor"],
        }
    ]
    attribution = "Nacionalinė mokėjimo agentūra prie Žemės ūkio ministerijos"
    crop_code_list = ec_url("lt_2021.csv")
    sources = {
        "https://zenodo.org/records/14384070/files/LT_2024.zip?download=1": [
            "GSA-LT-2024.geoparquet"
        ]
    }
