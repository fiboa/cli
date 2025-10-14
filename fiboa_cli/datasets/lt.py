from fiboa_cli.datasets.commons.euro_land import EuroLandBaseConverter


class LTConverter(EuroLandBaseConverter):
    id = "lt"
    short_name = "Lithuania"
    title = "Lithuania crop fields"
    description = "Collection of data on agricultural land and crop areas, cultivated crops in the territory of the Republic of Lithuania"

    provider = "Nacionalinė mokėjimo agentūra prie Žemės ūkio ministerijos <https://www.nma.lt>"
    attribution = "Nacionalinė mokėjimo agentūra prie Žemės ūkio ministerijos"
    ec_mapping_csv = "lt_2021.csv"
    sources = {
        "https://zenodo.org/records/14384070/files/LT_2024.zip?download=1": [
            "GSA-LT-2024.geoparquet"
        ]
    }
