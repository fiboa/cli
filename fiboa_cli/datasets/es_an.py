from .commons.data import read_data_csv
from ..convert_utils import convert as convert_
from .es import code_filter, ADD_COLUMNS, EXTENSIONS

import numpy as np

formats = {
    2024: "https://www.juntadeandalucia.es/ssdigitales/festa/agriculturapescaaguaydesarrollorural/2024/SP24_REC_{code}.zip",
    2023: "https://www.juntadeandalucia.es/ssdigitales/festa/agriculturapescaaguaydesarrollorural/2023/SP23_REC_{code}.zip",
    2022: "https://www.juntadeandalucia.es/export/drupaljda/01_SP22_REC_PROV_{code}.zip",
    2021: "https://www.juntadeandalucia.es/export/drupaljda/V1_01_SP21_REC_PROV_{code}.zip",
    2020: "https://www.juntadeandalucia.es/export/drupaljda/SP20_REC_PROV_{filename}.zip",
    2019: "https://www.juntadeandalucia.es/export/drupaljda/SIGPAC2019_REC_PROV_{filename}.zip",
    2018: "https://www.juntadeandalucia.es/export/drupaljda/SIGPAC2018_REC_PROV_{filename}.zip",
    2017: "https://www.juntadeandalucia.es/export/drupaljda/sp17_rec_{code}.zip",
}
EXTENSIONS = EXTENSIONS + ['https://fiboa.github.io/administrative-division-extension/v0.1.0/schema.yaml']

ID = "es_an"
SHORT_NAME = "Spain Andalusia"
TITLE = "Spain Andalusia Crop fields"
DESCRIPTION = """

https://www.juntadeandalucia.es/sites/default/files/inline-files/2024/03/Metadatos_Recintos_Sigpac_2024.pdf
Example; http://ws128.juntadeandalucia.es/agriculturaypesca/sigpac/index.xhtml
"""
PROVIDERS = [
    {
        "name": "Junta de Andalucía",
        "url": "https://www.juntadeandalucia.es/",
        "roles": ["producer", "licensor"]
    }
]
ATTRIBUTION = "©Junta de Andalucía"
# The end user is required to be informed, ..., that the cartography and geographic information is available free of charge on the website of the Ministry of Agriculture, Fisheries and Rural Development.
LICENSE = {
    # CC-SA-BY-ND
    "title": "Pursuant to Law 37/2007 of 16 November on the reuse of public sector information and Law 3/2013 of 24 July approving the Statistical and Cartographic Plan of Andalusia 2013-2017, the geographic information of SIGPAC is made available to the public.",
    "href": "https://www.juntadeandalucia.es/organismos/agriculturapescaaguaydesarrollorural/servicios/sigpac/visor/paginas/sigpac-descarga-informacion-geografica-shapes-provincias.html#toc-condiciones-de-uso-para-la-licencia-de-uso-comercial",
    "type": "text/html",
    "rel": "license"
}
COLUMNS = {
    "geometry": "geometry",
    "ID_RECINTO": "id",
    "CD_PROV": "admin_province_code",
    "CD_MUN": "admin_municipality_code",
    "NU_AREA": "area",
    "CD_USO": "crop:code",
    "crop:name": "crop:name",
    "crop:name_en": "crop:name_en",
}
def migrate(gdf):
    # This actually is a land use code. Not sure if we should put this in crop:code
    rows = read_data_csv("es_coda_uso.csv")
    mapping = {row["original_code"]: row["original_name"] for row in rows}
    mapping_en = {row["original_code"]: row["name_en"] for row in rows}
    gdf['crop:name'] = gdf['CD_USO'].map(mapping)
    gdf['crop:name_en'] = gdf['CD_USO'].map(mapping_en)
    gdf['NU_AREA'] = np.where(gdf['NU_AREA'] == 0, gdf['geometry'].area / 10000, gdf['NU_AREA'] / 10000)
    return gdf


ADD_COLUMNS = ADD_COLUMNS | {
    "determination_datetime": "2024-03-28T00:00:00Z",
    "admin:country_code": "ES",
    "admin:subdivision_code": "AN"
}

MISSING_SCHEMAS = {
    "properties": {
        "admin_province_code": {
            "type": "string"
        },
        "admin_municipality_code": {
            "type": "string"
        },
    }
}


def convert(output_file, cache = None, **kwargs):
    year = 2024  # TODO make variable
    data = read_data_csv("es_an_prv.csv")

    def fname(line):
        return f"SP{year % 100}_REC_{line['code']}.shp"

    sources = {
        formats[year].format(**line): [fname(line)]
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
        column_additions=ADD_COLUMNS,
        extensions=EXTENSIONS,
        migration=migrate,
        providers=PROVIDERS,
        column_filters={"CD_USO": code_filter},
        missing_schemas=MISSING_SCHEMAS,
        attribution=ATTRIBUTION,
        license=LICENSE,
        **kwargs
    )
