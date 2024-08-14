from ..convert_utils import convert as convert_
from .commons.ec import add_eurocrops
from . import fr as base

SOURCES = {
    "https://zenodo.org/records/10118572/files/FR_2018.zip": [
        "FR_2018/FR_2018_EC21.shp"
    ]
}

ID, SHORT_NAME, TITLE, DESCRIPTION, PROVIDERS, EXTENSIONS, COLUMNS, LICENSE = add_eurocrops(base, 2018)

def convert(output_file, input_files = None, cache = None, source_coop_url = None, collection = False, compression = None):
    convert_(
        output_file,
        cache,
        SOURCES,
        COLUMNS,
        ID,
        TITLE,
        DESCRIPTION,
        extensions=EXTENSIONS,
        input_files=input_files,
        providers=PROVIDERS,
        source_coop_url=source_coop_url,
        missing_schemas=base.MISSING_SCHEMAS,
        column_filters=base.COLUMN_FILTERS,
        attribution=base.ATTRIBUTION,
        store_collection=collection,
        license=LICENSE,
        compression=compression,
        explode_multipolygon=True
    )
