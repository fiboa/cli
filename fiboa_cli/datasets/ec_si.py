from ..convert_utils import convert as convert_

SOURCES = {
  "https://zenodo.org/records/10118572/files/SI_2021.zip?download=1": ["SI_2021_EC21.shp"]
}

ID = "ec_si"
SHORT_NAME = "Slovenia (Eurocrops, 2021)"
TITLE = "Field boundaries for Slovenia from EuroCrops (2021)"
DESCRIPTION = """
This dataset contains the field boundaries for all of Slovenia in 2021. The data was collected by the Slovenian government and harmonized
by the EuroCrops project and is available on Zenodo.

EuroCrops is a dataset collection combining all publicly available self-declared crop reporting datasets from countries of the European Union.
The project is funded by the German Space Agency at DLR on behalf of the Federal Ministry for Economic Affairs and Climate Action (BMWK).
The work is licensed under a [Creative Commons Attribution-ShareAlike 4.0 International License][https://creativecommons.org/licenses/by-sa/4.0/].

The project developed a new **Hierarchical Crop and Agriculture Taxonomy (HCAT)** that harmonises all declared crops across the European Union.
In the data you'll find this as additional attributes:

- `EC_trans_n`: The original crop name translated into English
- `EC_hcat_n`: The machine-readable HCAT name of the crop
- `EC_hcat_c`: The 10-digit HCAT code indicating the hierarchy of the crop
"""

PROVIDER_NAME = "EuroCrops"
PROVIDER_URL = "https://github.com/maja601/EuroCrops/wiki/Slovenia"
ATTRIBUTION = "Ministrstvo za kmetijstvo, gozdarstvo in prehrano"

LICENSE = "CC-BY-4.0"

COLUMNS = {
    'geometry': 'geometry', #fiboa core field
    'ID': 'id', #fiboa core field
    'AREA': 'area', #fiboa core field
    'GERK_PID': 'gerk_pid', #fiboa custom field
    'SIFRA_KMRS': 'crop_type_class', #fiboa custom field
    'RASTLINA': 'rastlina', #fiboa custom field
    'CROP_LAT_E': 'crop_lat_e', #fiboa custom field
    'COLOR': 'color', #fiboa custom field
    'EC_trans_n': 'EC_trans_n', #fiboa custom field
    'EC_hcat_n': 'EC_hcat_n', #fiboa custom field
    'EC_hcat_c': 'EC_hcat_c' #fiboa custom field
}

ADD_COLUMNS = {
    "determination_datetime": "2021-10-06T00:00:00Z"
}

MISSING_SCHEMAS = {
    'required': ['gerk_pid', 'crop_type_class', 'rastlina', 'crop_latin', 'color', 'EC_trans_n','EC_hcat_n'],
    'properties': {
        'gerk_pid': {
            'type': 'uint64'
        },
        'crop_type_class': {
            'type': 'string'
        },
        'rastlina': {
            'type': 'string'
        },
        'crop_lat_e': {
            'type': 'string'
        },
        'color': {
            'type': 'string'
        },
        'EC_trans_n': {
            'type': 'string'
        },
        'EC_hcat_n': {
            'type': 'string'
        },
        'EC_hcat_c': {
            'type': 'uint32'
        }
    }
}


def convert(output_file, input_files = None, cache = None, source_coop_url = None, collection = False, compression = None):
    convert_(
        output_file,
        cache,
        SOURCES,
        COLUMNS,
        ID,
        TITLE,
        DESCRIPTION,
        input_files=input_files,
        provider_name=PROVIDER_NAME,
        provider_url=PROVIDER_URL,
        source_coop_url=source_coop_url,
        missing_schemas=MISSING_SCHEMAS,
        column_additions=ADD_COLUMNS,
        attribution=ATTRIBUTION,
        store_collection=collection,
        license=LICENSE,
        compression=compression,
    )
