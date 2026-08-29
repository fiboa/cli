"""EuroCropsV2 — Italy, Tuscany (NUTS-2: ITI1).

Single-region Italian converter using the harmonised, multi-year GeoParquet
release published by the JRC at
``https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DRLL/EuroCropsV2/gpqtv201/``.

EuroCropsV2 itself is a separate dataset from the original (TUM) EuroCrops; it
covers Italy via Tuscany only at the moment (NUTS-2 ``ITI1``). HCAT3 names
and codes are joined in at conversion time from the EuroCropsV2 mapping table.

See the wider survey at
``fiboa-data-survey/data/EU-EuroCropsV2.md`` for the full picture.
"""

from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin

JRC_BASE = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/DRLL/EuroCropsV2/gpqtv201"
NUTS = "iti1"


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    id = "it_1"
    short_name = "Italy, Tuscany"
    title = "Italy Tuscany (ITI1) Crop Fields — EuroCropsV2"
    description = """
EuroCropsV2 harmonised Geo-Spatial Application (GSA) declarations for Tuscany (NUTS-2: ITI1), Italy. Produced by
the JRC, EUROSTAT and Technical University of Munich from the Italian paying agency's parcel-level crop
declarations.

The source is distributed as one GeoParquet per year (2016-2023) in EPSG:3035 (LAEA Europe). HCAT3 names and
codes are joined in from the EuroCropsV2 NUTS mapping table at conversion time.
    """
    provider = (
        "Joint Research Centre, European Commission "
        "<https://data.jrc.ec.europa.eu/dataset/b9fb9e67-78a9-4327-9d59-39a928d812d3>"
    )
    attribution = "European Commission, Joint Research Centre — EuroCropsV2"
    license = "CC-BY-4.0"
    variants = {str(y): f"{JRC_BASE}/{NUTS}_{y}.parquet" for y in reversed(range(2016, 2024))}

    admin_country_code = "IT"
    admin_subdivision_code = "1"
    ec_mapping_csv = "https://fiboa.org/code/it/iti1.csv"
    columns = {
        "geometry": "geometry",
        "cropfield": "id",
        "area_ha": "metrics:area",
        "original_code": "crop:code",
    }
