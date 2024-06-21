from ..convert_utils import convert as convert_
import pandas as pd

SOURCES = None
DATA_ACCESS = """
To download the data, create an account at <https://geoportail.wallonie.be/>. Go to the dataset at <https://geoportail.wallonie.be/catalogue/49294570-2a8d-49ca-995c-1b0890672bc8.html>. Select 'Accès' and add the data to your downloads (click 'AJOUTER À MES TÉLÉCHARGEMENTS'). Then finish the download through 'finalisez votre demande de téléchargement' at <https://geoportail.wallonie.be/geodata-donwload.html> and select the required data format and projection. Choose 'OGC GeoPackage (.gpkg)' in 'Belge 1972 / Belgian Lambert 72'.
Select 'Region Wallone' at 'DÉCOUPAGE' for the full dataset. Select 'Je souhaite une license' to acquire a license. Indicate whether it's Professional or Personal ('particulier') use and choose an end-date of the license. You will receive an e-mail with the license and another e-mail with a link to the data.
Either extract the ZIP file and point to the GeoPackage file or use the `-i` command to extract and pick the `SIGEC_PARC_AGRI_ANON__2022.gpkg` from the ZIP file (e.g. `-i SIGEC_PARC_AGRI_ANON__2022_GEOPACKAGE_31370.zip=SIGEC_PARC_AGRI_ANON__2022.gpkg`)
"""

ID = "be_wa"
SHORT_NAME = "Belgium, Wallonia"
TITLE = "Belgium Wallonia: Parcellaire Agricole Anonyme"
DESCRIPTION = """
The Crop Fields (PAA) covers land use in agricultural and forestry areas managed as part of the implementation of the Common Agricultural Policy by the Paying Agency of Wallonia.

The PAA represents the public version of the agricultural plot. It therefore does not include personal information allowing the operator to be identified. It is provided on an annual basis. Data from a year of cultivation are made available to the public during the following year.

You can download the data yourself, but the license does not allow public distribution. You can obtain a personal/company license for free, or freely use a WMS service for visualization.
"""

PROVIDER_NAME = "Service public de Wallonie (SPW)"
PROVIDER_URL = "https://geoportail.wallonie.be/catalogue/49294570-2a8d-49ca-995c-1b0890672bc8.html"
ATTRIBUTION = "Service public de Wallonie (SPW)"

LICENSE = {
    "title": "Conditions générales d'utilisation des données géographiques numériques du Service public de Wallonie",
    "href": "https://geoportail.wallonie.be/files/documents/ConditionsSPW/DataSPW-CGU.pdf",
    "type": "text/html",
    "rel": "license"
}

COLUMNS = {
    "geometry": "geometry",
    "OBJECTID": "id",
    "SURF_HA": "area",
    "CAMPAGNE": "determination_datetime",
    'CULT_COD': 'crop_code',
    'CULT_NOM': 'crop_name',
    'GROUPE_CULT': 'group_code',
}

COLUMN_MIGRATIONS = {
    "determination_datetime": lambda col: pd.to_datetime(col, format='%Y') + pd.DateOffset(months=4, days=14)
}

MISSING_SCHEMAS = {
    "properties": {
        "crop_code": {
            "type": "string"
        },
        "crop_name": {
            "type": "string"
        },
        "group_code": {
            "type": "string"
        },
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
        column_migrations=COLUMN_MIGRATIONS,
        attribution=ATTRIBUTION,
        store_collection=collection,
        license=LICENSE,
        compression=compression,
    )
