from ..convert_utils import convert as convert_

SOURCES = {
  "https://www.landbouwvlaanderen.be/bestanden/gis/Landbouwgebruikspercelen_2023_-_Definitief_(extractie_28-03-2024)_GPKG.zip": ["Landbouwgebruikspercelen_2023_-_Definitief_(extractie_28-03-2024).gpkg"]
}

ID = "be_vlg"
SHORT_NAME = "Belgium, Flanders"
TITLE = "Crop field boundaries for Belgium - Flanders"
DESCRIPTION = """
Since 2020, the Department of Agriculture and Fisheries has been publishing a more extensive set of data related to agricultural use plots (from the 2008 campaign).

From 2023, the downloadable dataset of agricultural use plots will also include the specialization given by the company (= company typology) and that is given to the plots of the company. Based on the typology, the companies are divided into 4 major specializations: arable farming, horticulture, livestock farming and mixed farms. The specialization of each company is calculated annually according to a European method and is based on the standard output of the various agricultural productions on the company. It is therefore an economic specialization and not a reflection of all agricultural production on the company.
"""

PROVIDERS = [
    {
        "name": "Agentschap Landbouw & Zeevisserij (Government)",
        "url": "https://landbouwcijfers.vlaanderen.be/open-geodata-landbouwgebruikspercelen",
        "roles": ["producer", "licensor"]
    }
]

"""
The following publication urls use license https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0
This license is documented at https://www.vlaanderen.be/digitaal-vlaanderen/onze-oplossingen/open-data/voorwaarden-voor-het-hergebruik-van-overheidsinformatie/modellicentie-gratis-hergebruik
This documentation states the license is compatible with Creative Commons Attribution license 3.0 (CC BY 3.0)

- https://metadata.vlaanderen.be/srv/dut/catalog.search#/metadata/ae94435d-1ffb-451b-9c8b-d7e8c2d42dc2
- https://metadata.vlaanderen.be/srv/dut/catalog.search#/metadata/21dda3b2-6e27-4bf3-af34-013854331f41

Bronvermeldingsvoorschrift (Attribution requirement): "Bron: Dept. LV"
"""

ATTRIBUTION = "Bron: Dept. LV"
# License is https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0, which is compatible with CC-BY-3.0
LICENSE = {"title": "Licentie modellicentie-gratis-hergebruik/v1.0", "href": "https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0", "type": "text/html", "rel": "license"}

# TODO we skip many, specific columns. Check the data survey or included documentation for more available columns
COLUMNS = {
    "geometry": "geometry",
    "BT_BRON": "source",
    "BT_OMSCH": "typology",
    "GRAF_OPP": "area",
    "REF_ID": "id",
    "GWSCOD_H": "crop_code",
    "GWSNAM_H": "crop_name",
}

ADD_COLUMNS = {
    "determination_datetime": "2024-03-28T00:00:00Z"
}

EXTENSIONS = []
COLUMN_MIGRATIONS = {}
COLUMN_FILTERS = {}

MIGRATION = None

MISSING_SCHEMAS = {
    "properties": {
        "source": {
            "type": "string"
        },
        "crop_code": {
            "type": "string"
        },
        "crop_name": {
            "type": "string"
        },
        "typology": {
            "type": "string"
        }
    }
}


# Conversion function, usually no changes required
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
        extensions=EXTENSIONS,
        missing_schemas=MISSING_SCHEMAS,
        column_additions=ADD_COLUMNS,
        column_migrations=COLUMN_MIGRATIONS,
        column_filters=COLUMN_FILTERS,
        migration=MIGRATION,
        attribution=ATTRIBUTION,
        store_collection=collection,
        license=LICENSE,
        compression=compression
    )
