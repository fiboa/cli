from ..convert_utils import convert as convert_

SOURCES = {
    "https://data.source.coop/kerner-lab/fields-of-the-world-slovakia/boundaries_slovakia_2021.parquet": "boundaries_slovakia_2021.parquet",
    "https://data.source.coop/kerner-lab/fields-of-the-world-rwanda/boundaries_rwanda_2021.parquet": "boundaries_rwanda_2021.parquet",
    "https://data.source.coop/kerner-lab/fields-of-the-world-portugal/boundaries_portugal_2021.parquet": "boundaries_portugal_2021.parquet",
    "https://data.source.coop/kerner-lab/fields-of-the-world-slovenia/boundaries_slovenia_2021.parquet": "boundaries_slovenia_2021.parquet",
    "https://data.source.coop/kerner-lab/fields-of-the-world-vietnam/boundaries_vietnam_2021.parquet": "boundaries_vietnam_2021.parquet",
    "https://data.source.coop/kerner-lab/fields-of-the-world-sweden/boundaries_sweden_2021.parquet": "boundaries_sweden_2021.parquet",
    "https://data.source.coop/kerner-lab/fields-of-the-world-spain/boundaries_spain_2020.parquet": "boundaries_spain_2020.parquet",
    "https://data.source.coop/kerner-lab/fields-of-the-world-southafrica/boundaries_south_africa_2018.parquet": "boundaries_south_africa_2018.parquet",
    "https://data.source.coop/kerner-lab/fields-of-the-world-netherlands/boundaries_netherlands_2022.parquet": "boundaries_netherlands_2022.parquet",
    "https://data.source.coop/kerner-lab/fields-of-the-world-luxembourg/boundaries_luxembourg_2022.parquet": "boundaries_luxembourg_2022.parquet",
    "https://data.source.coop/kerner-lab/fields-of-the-world-lithuania/boundaries_lithuania_2021.parquet": "boundaries_lithuania_2021.parquet",
    "https://data.source.coop/kerner-lab/fields-of-the-world-latvia/boundaries_latvia_2021.parquet": "boundaries_latvia_2021.parquet",
    "https://data.source.coop/kerner-lab/fields-of-the-world-kenya/boundaries_kenya_2022.parquet": "boundaries_kenya_2022.parquet",
    "https://data.source.coop/kerner-lab/fields-of-the-world-india/boundaries_india_2016.parquet": "boundaries_india_2016.parquet",
    "https://data.source.coop/kerner-lab/fields-of-the-world-germany/boundaries_germany_2018_2019.parquet": "boundaries_germany_2018_2019.parquet",
    "https://data.source.coop/kerner-lab/fields-of-the-world-france/boundaries_france_2020.parquet": "boundaries_france_2020.parquet",
    "https://data.source.coop/kerner-lab/fields-of-the-world-finland/boundaries_finland_2021.parquet": "boundaries_finland_2021.parquet",
    "https://data.source.coop/kerner-lab/fields-of-the-world-estonia/boundaries_estonia_2021.parquet": "boundaries_estonia_2021.parquet",
    "https://data.source.coop/kerner-lab/fields-of-the-world-denmark/boundaries_denmark_2021.parquet": "boundaries_denmark_2021.parquet",
    "https://data.source.coop/kerner-lab/fields-of-the-world-croatia/boundaries_croatia_2023.parquet": "boundaries_croatia_2023.parquet",
    "https://data.source.coop/kerner-lab/fields-of-the-world-corsica/boundaries_corsica_2021.parquet": "boundaries_corsica_2021.parquet",
    "https://data.source.coop/kerner-lab/fields-of-the-world-cambodia/boundaries_cambodia_2021.parquet": "boundaries_cambodia_2021.parquet",
    "https://data.source.coop/kerner-lab/fields-of-the-world-brazil/boundaries_brazil_2020.parquet": "boundaries_brazil_2020.parquet",
    "https://data.source.coop/kerner-lab/fields-of-the-world-belgium/boundaries_belgium_2021.parquet": "boundaries_belgium_2021.parquet",
    "https://data.source.coop/kerner-lab/fields-of-the-world-austria/boundaries_austria_2021.parquet": "boundaries_austria_2021.parquet",
}

LICENSES = {
    "austria": "CC-BY-4.0",
    "belgium": "https://metadata.vlaanderen.be/srv/dut/catalog.search#/metadata/d869db4a-73f4-470e-b5ca-a0f7cd3ab585",
    "brazil": "CC-BY-4.0",
    "cambodia": "CC-BY-4.0",
    "corsica": "CC-BY-2.0",
    "croatia": "https://www.apprrr.hr/wp-content/uploads/2024/01/Otvoreni-podaci-APPRRR.docx",
    "denmark": "CC0-1.0",
    "estonia": "CC-3.0",
    "finland": "CC-BY-4.0",
    "france": "https://geoservices.ign.fr/sites/default/files/2021-07/DC_DL_RPG_1-0.pdf",
    "germany": "DL-DE/BY-2-0",
    "india": "CC-BY-4.0",
    "kenya": "GPL-2.0-or-later",
    "latvia": "CC-BY-NC-4.0",
    "lithuania": "https://www.geoportal.lt/metadata-catalog/catalog/search/resource/details.page?uuid=%7B7AF3F5B2-DC58-4EC5-916C-813E994B2DCF%7D",
    "luxembourg": "CC0-1.0",
    "netherlands": "CC0-1.0",
    "portugal": "CC-BY-NC-4.0",
    "rwanda": "CC-BY-4.0",
    "slovakia": "CC0-1.0",
    "slovenia": "CC-BY-4.0",
    "southafrica": "CC-BY-NC-SA-4.0",
    "spain": "CC-BY-4.0",
    "sweden": "https://www.geodata.se/geodataportalen/srv/swe/catalog.search;jsessionid=6C2D281619D69AC2356E1BD4C1923A3A#/metadata/df439ba5-014e-44ec-86cb-ddb9e5ba306c",
    "vietnam": "CC-BY-4.0",
}

ID = "ftw"
SHORT_NAME = "Fields of the World"
TITLE = "Fields of the World (source data)"
DESCRIPTION = "The field boundaries that were used to create the Field of the World ML dataset."

PROVIDERS = [
    {
        "name": "Fields of the World",
        "url": "https://fieldsofthe.world/",
        "roles": ["processor"]
    }
]

LICENSE = "various"

COLUMNS = {
    "id": "id",
    "geometry": "geometry",
    "determination_datetime": "determination_datetime",
    "area": "area",
    "perimeter": "perimeter",
    "dataset": "dataset",
    "license": "license",
}

def FILE_MIGRATION(gdf, path: str, uri: str, layer: str = None):
    dataset = uri.replace("https://data.source.coop/kerner-lab/fields-of-the-world-", "").split("/")[0]
    gdf["dataset"] = dataset
    license = LICENSES.get(dataset, None)
    if license is None:
        print(f"WARNING: License for {dataset} not found")
    gdf["license"] = license
    return gdf

MISSING_SCHEMAS = {
    "required": ["dataset", "license"],
    "properties": {
        "dataset": {
            "type": "string"
        },
        "license": {
            "type": "string"
        }
    }
}

def convert(output_file, cache = None, **kwargs):
    convert_(
        output_file,
        cache,
        SOURCES,
        COLUMNS,
        ID,
        TITLE,
        DESCRIPTION,
        providers=PROVIDERS,
        missing_schemas=MISSING_SCHEMAS,
        file_migration=FILE_MIGRATION,
        license=LICENSE,
        **kwargs
    )
