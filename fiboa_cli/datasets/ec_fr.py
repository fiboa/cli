from ..convert_utils import convert as convert_

SOURCES = {
  "https://zenodo.org/records/10118572/files/FR_2018.zip": ["FR_2018/FR_2018_EC21.shp"]
}

ID = "ec_fr"
SHORT_NAME = "France (Eurocrops, 2018)"
TITLE = "Field boundaries for France from EuroCrops (2018)"
DESCRIPTION = """
This dataset contains the field boundaries for all of France in 2018. The data was collected by the French government and harmonized
by the EuroCrops project and is available on Zenodo.

EuroCrops is a dataset collection combining all publicly available self-declared crop reporting datasets from countries of the European Union.
The project is funded by the German Space Agency at DLR on behalf of the Federal Ministry for Economic Affairs and Climate Action (BMWK).
The work is licensed under a [Creative Commons Attribution-ShareAlike 4.0 International License][cc-by-sa].

The project developed a new **Hierarchical Crop and Agriculture Taxonomy (HCAT)** that harmonises all declared crops across the European Union.
In the data you'll find this as additional attributes:

- `EC_trans_n`: The original crop name translated into English
- `EC_hcat_n`: The machine-readable HCAT name of the crop
- `EC_hcat_c`: The 10-digit HCAT code indicating the hierarchy of the crop
"""

PROVIDERS = [
    {
        "name": "EuroCrops",
        "url": "https://github.com/maja601/EuroCrops/wiki/France",
        "roles": ["producer", "licensor"]
    }
]
ATTRIBUTION = "Institut National de l'Information Géographique et Forestière"

LICENSE = "CC-BY-4.0"

COLUMNS = {
    'geometry': 'geometry', #fiboa core field
    'ID_PARCEL': 'id', #fiboa core field
    'SURF_PARC': 'area', #fiboa core field
    'CODE_CULTU': 'code_culture', #fiboa custom field
    'CODE_GROUP': 'code_group', #fiboa custom field
    'EC_trans_n': 'EC_trans_n', #fiboa custom field
    'EC_hcat_n': 'EC_hcat_n', #fiboa custom field
    'EC_hcat_c': 'EC_hcat_c' #fiboa custom field
}

ADD_COLUMNS = {
  "determination_datetime": "2018-01-15T00:00:00Z"
}

MISSING_SCHEMAS = {
    'required': ['code_culture', 'code_group', 'EC_trans_n','EC_hcat_n', 'EC_hcat_c'],
    'properties': {
        'code_culture': {
            'type': 'string'
        },
        'code_group': {
            'type': 'uint16'
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
        providers=PROVIDERS,
        source_coop_url=source_coop_url,
        missing_schemas=MISSING_SCHEMAS,
        column_additions=ADD_COLUMNS,
        attribution=ATTRIBUTION,
        store_collection=collection,
        license=LICENSE,
        compression=compression,
    )
