import csv

from .commons.data import read_data_csv
from ..convert_utils import convert as convert_
from .es import code_filter, ADD_COLUMNS, EXTENSIONS

ID = "es_cl"
SHORT_NAME = "Spain Castilla y León"
TITLE = "Spain Castile and León Crop fields"
DESCRIPTION = """
Official SIGPAC land plan for the year 2024. (reference date 02-01-2024)

Source: SIGPAC (FEGA) database. The Land Consolidation Replacement Farms are included,
not updated in the SIGPAC published in the Viewer.
Data manager: Ministry of Agriculture, Fisheries and Food.
Data provided by: Department of Agriculture, Livestock and Rural Development. Regional Government of Castile and Leon.
Free use of the data is permitted, but commercial exploitation is prohibited.
"""
PROVIDERS = [
    {
        "name": "Department of Agriculture, Livestock and Rural Development. Regional Government of Castile and Leon",
        "url": "https://www.itacyl.es/",
        "roles": ["producer", "licensor"]
    }
]
LICENSE = "CC-NC"  # Free use of the data is permitted, but commercial exploitation is prohibited.
COLUMNS = {
    "geometry": "geometry",
    "determination_datetime": "determination_datetime",
    "crop:code": "USO_SIGPAC",
    "crop:name": "crop:name",
    "crop:name_en": "crop:name_en",
}
ADD_COLUMNS = ADD_COLUMNS | {
    "determination_datetime": "2024-01-01T00:00:00Z"
}


def migrate(gdf):
    gdf.geometry = gdf.geometry.force_2d()
    # This actually is a land use code. Not sure if we should put this in crop:code
    rows = read_data_csv("es_coda_uso.csv")
    mapping = {row["original_code"]: row["original_name"] for row in rows}
    mapping_en = {row["original_code"]: row["name_en"] for row in rows}
    gdf['crop:name'] = gdf['USO_SIGPAC'].map(mapping)
    gdf['crop:name_en'] = gdf['USO_SIGPAC'].map(mapping_en)
    return gdf


def convert(output_file, cache = None, **kwargs):
    year = 2024  # TODO make variable
    data = read_data_csv("es_cl_prv.csv")

    def fname(line):
        if line['code'] == "24":  # hack, we should be able to override filename-filtering
            return [f"{line['code']}_RECFE_ESTE.shp", f"{line['code']}_RECFE_OESTE.shp"]
        elif line['code'] == "09":
            return [f"{line['code']}_RECFE_NORTE.shp", f"{line['code']}_RECFE_SUR.shp"]
        return [f"{line['filename']}/{line['code']}_RECFE.shp"]

    sources = {
        f"http://ftp.itacyl.es/cartografia/05_SIGPAC/{year}_ETRS89/Parcelario_SIGPAC_CyL_Provincias/{line['filename']}.zip": fname(line)
        for line in data
    }

    convert_(
        output_file,
        cache,
        sources,
        COLUMNS,
        ID,
        TITLE,
        DESCRIPTION,
        providers=PROVIDERS,
        extensions=EXTENSIONS,
        column_filters={"USO_SIGPAC": code_filter},
        migration=migrate,
        license=LICENSE,
        index_as_id=True,
        **kwargs
    )
