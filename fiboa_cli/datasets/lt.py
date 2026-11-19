from fiboa_cli.datasets.commons.encoding import repair_cp1257
from fiboa_cli.datasets.commons.euro_land import EuroLandBaseConverter

BASE = "https://zenodo.org/records/18670815/files"


class LTConverter(EuroLandBaseConverter):
    id = "lt"
    short_name = "Lithuania"
    title = "Lithuania crop fields"
    description = "Collection of data on agricultural land and crop areas, cultivated crops in the territory of the Republic of Lithuania"

    provider = "Nacionalinė mokėjimo agentūra prie Žemės ūkio ministerijos <https://www.nma.lt>"
    attribution = "Nacionalinė mokėjimo agentūra prie Žemės ūkio ministerijos"
    # The table spells the names correctly. The source carries HCAT itself; the table
    # also corrects it where it differs, which are two crops Europe-LAND mapped to HCAT2
    # classes (pulses to spring cereals, wetlands to spinach).
    hcat_mapping_csv = "https://fiboa.org/code/lt/lt_2021.csv"
    hcat_mapping_supplements = [hcat_mapping_csv]
    # Europe-LAND v1.3 (record 18670815, February 2026) bundles both editions in
    # one archive; v1.1 (record 14384070), which this converter used to read,
    # carried 2024 alone.
    variants = {
        str(year): {f"{BASE}/LT_years_2024-2025.zip": [f"GSA-LT-{year}.geoparquet"]}
        for year in (2025, 2024)
    }
    # Europe-LAND decoded the CP1257 names as Latin-1 (`Þieminiai javai`)
    column_migrations = {
        "crop_code": lambda col: col.map(repair_cp1257),
        "crop_name": lambda col: col.map(repair_cp1257),
    }
