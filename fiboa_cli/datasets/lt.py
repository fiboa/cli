from fiboa_cli.datasets.commons.euro_land import EuroLandBaseConverter

BASE = "https://zenodo.org/records/18670815/files"


class LTConverter(EuroLandBaseConverter):
    id = "lt"
    short_name = "Lithuania"
    title = "Lithuania crop fields"
    description = "Collection of data on agricultural land and crop areas, cultivated crops in the territory of the Republic of Lithuania"

    provider = "Nacionalinė mokėjimo agentūra prie Žemės ūkio ministerijos <https://www.nma.lt>"
    attribution = "Nacionalinė mokėjimo agentūra prie Žemės ūkio ministerijos"
    ec_mapping_csv = "lt_2021.csv"
    # Europe-LAND v1.3 (record 18670815, February 2026) bundles both editions in
    # one archive; v1.1 (record 14384070), which this converter used to read,
    # carried 2024 alone.
    variants = {
        str(year): {f"{BASE}/LT_years_2024-2025.zip": [f"GSA-LT-{year}.geoparquet"]}
        for year in (2025, 2024)
    }
    # The inventory carries no per-feature date, so the edition is the year.
    use_variant_as_determination = True
