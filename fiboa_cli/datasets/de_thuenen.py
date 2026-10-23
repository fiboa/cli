from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin

RECORD = "https://zenodo.org/api/records/10619783/files"

# Classes of the open landscape that are no field: hedges and tree rows, and land that is
# neither farmed nor fallow
NOT_FIELDS = {"3001", "3004"}


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    variants = {
        str(year): {f"{RECORD}/CTM_GER_{year}_seg_v201.fgb/content": f"CTM_GER_{year}_seg_v201.fgb"}
        for year in range(2021, 2016, -1)
    }

    id = "de_thuenen"
    short_name = "Germany (Thünen)"
    title = "Crop type map of Germany from Sentinel-1, Sentinel-2 and Landsat (Thünen Institute)"
    description = """
The Thünen Institute's annual map of agricultural land use in Germany: the dominant crop type or
land use of every field in the open landscape, classified from time series of Sentinel-1,
Sentinel-2 and Landsat 8 (Blickensdörfer et al., 2022). The classified raster was aggregated into
homogeneous objects (Tetteh et al., 2021, 2023), so the boundaries are inferred from imagery, not
declared by farmers. Small woody features and other areas that are no field are left out.
    """
    provider = "Johann Heinrich von Thünen-Institut <https://doi.org/10.5281/zenodo.10619783>"
    attribution = (
        "Tetteh, G.O., Schwieder, M., Blickensdörfer, L., Gocht, A., Erasmi, S. (2024): "
        "Agricultural land use (vector): National-scale crop type maps for Germany, v201, "
        "Thünen-Institut, doi:10.5281/zenodo.10619783"
    )
    license = "CC-BY-4.0"

    extensions = {"https://fiboa.org/crop-extension/v0.2.0/schema.yaml"}
    hcat_mapping_csv = "https://fiboa.org/code/de/thuenen/ctm.csv"

    columns = {
        "geometry": "geometry",
        "id": "id",
        "area_ha": "metrics:area",
        "ctm_majority": "crop:code",
        "crop_type": "crop:name",
    }
    column_migrations = {
        # the class code is stored as a float, e.g. 1101.0
        "ctm_majority": lambda col: col.astype("Int64").astype("string"),
    }
    column_filters = {
        "ctm_majority": lambda col: ~col.astype("Int64").astype("string").isin(NOT_FIELDS),
    }
