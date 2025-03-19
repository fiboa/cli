from os.path import dirname, join

from ..convert_utils import BaseConverter
from .commons.admin import AdminConverterMixin
from .commons.ec import load_ec_mapping


class Converter(AdminConverterMixin, BaseConverter):
    sources = {
        "https://data.cnra.ca.gov/dataset/6c3d65e3-35bb-49e1-a51e-49d5a2cf09a9/resource/f38d3f6f-dcf1-4553-9f07-4f381d494320/download/i15_crop_mapping_2022_provisional_gdb.zip": [
            "i15_Crop_Mapping_2022_Provisional_GDB/i15_Crop_Mapping_2022_Provisional.gdb"
        ]
    }
    id = "us_ca_scm"
    admin_subdivision_code = "CA"
    short_name = "US, California (SCM)"
    title = "California (US) Statewide Crop Mapping"
    description = """
    For many years, the California Department of Water Resources (DWR) has collected land use data throughout the state
    and used this information to develop water use estimates for statewide and regional planning efforts, including water
    use projections, water use efficiency evaluation, groundwater model development, and water transfers. These data are
    essential for regional analysis and decision making, which has become increasingly important as DWR and other state agencies
    seek to address resource management issues, regulatory compliance issues, environmental impacts, ecosystem services,
    urban and economic development, and other issues.
    """
    extensions = {"https://fiboa.github.io/crop-extension/v0.1.0/schema.yaml"}
    providers = [
        {
            "name": "California Department of Water Resources",
            "url": "https://water.ca.gov/",
            "roles": ["licensor", "producer"],
        }
    ]
    license = "CC-0"
    columns = {
        "geometry": "geometry",
        "UniqueID": "id",
        "MAIN_CROP": "crop:code",
        "crop:name": "crop:name",
        "COUNTY": "admin_level_2",
    }
    column_additions = {
        "determination_datetime": "2023-05-01T00:00:00Z",
        "crop:code_list": "https://fiboa.org/code/us/ca/scm.csv",
    }
    missing_schemas = {
        "properties": {
            "admin_level_2": {"type": "string"},
        }
    }

    def migrate(self, gdf):
        """
        Perform migration on the GeoDataFrame to map crop names using a provided mapping file.
        """
        gdf = super().migrate(gdf)
        mapping = load_ec_mapping(url=join(dirname(__file__), "data-files", "us_ca_scm.csv"))
        original_name_mapping = {e["original_code"]: e["original_name"] for e in mapping}
        gdf["crop:name"] = gdf["MAIN_CROP"].map(original_name_mapping)
        return gdf
