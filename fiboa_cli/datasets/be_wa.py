from ..convert_gml import gml_assure_columns
from ..convert_utils import convert as convert_
from .commons.admin import add_admin

SOURCES = {
  "https://geoservices.wallonie.be/geotraitement/spwdatadownload/get/2a0d9be0-ac3d-443e-9db0-a7cfb0f128e2/LU_ExistingLandUse_SIGEC2022.gml.zip?blocksize=0": ["LU_ExistingLandUse_SIGEC2022.gml"]
}
LAYER = "ExistingLandUseObject"

ID = "be_wa"
SHORT_NAME = "Belgium, Wallonia"
TITLE = "Belgium Wallonia: Parcellaire Agricole Anonyme"
DESCRIPTION = """
The Crop Fields (PAA) covers land use in agricultural and forestry areas managed as part of the implementation of the
Common Agricultural Policy by the Paying Agency of Wallonia.

The PAA represents the public version of the agricultural plot. It therefore does not include personal information
allowing the operator to be identified. It is provided on an annual basis. Data from a year of cultivation are made
available to the public during the following year.

The data is distributed in two ways: either at the source of the paying agency (more attributes
but no public distribution) or at the European Commission data portal (no limitations). We use the
free-licensed version for this converter.
"""

PROVIDERS = [
    {
        "name": "Inspire Geoportal of the European Commission",
        "url": "https://inspire-geoportal.ec.europa.eu/srv/eng/catalog.search#/metadata/2a0d9be0-ac3d-443e-9db0-a7cfb0f128e2",
        "roles": ["host", "processor"]
    }
]

LICENSE = {
    "title": "No conditions apply to access and use. Distributed through Inspire guidelines",
    "href": "https://inspire-geoportal.ec.europa.eu/srv/eng/catalog.search#/metadata/2a0d9be0-ac3d-443e-9db0-a7cfb0f128e2",
    "type": "text/html",
    "rel": "license"
}

COLUMNS = {
    "geometry": "geometry",
    "crop_name": "crop_name",
    "crop_code": "crop_code",
    "id": "id",
    "determination_datetime": "determination_datetime",
}

MISSING_SCHEMAS = {
    "properties": {
        "crop_code": {
            "type": "string"
        },
        "crop_name": {
            "type": "string"
        },
    }
}

ADD_COLUMNS = {
    "determination_datetime": "2022-01-01T00:00:00Z"
}

COLUMN_MIGRATIONS = {
    # Extract last digits from crop_code, example crop_code is:
    # http://geoservices.wallonie.be/inspire/atom/LU_LandUseClassification_LPIS.xml?code=#LandUseClass.lpis.cropCategory.6
    "crop_code": lambda col: col.str.extract(r'\.(\d+)$', expand=False),
    "crop_name": lambda col: col.str.strip()  # .str.replace("  ", " ").str.replace("( ", "(")
}

COLUMNS, ADD_COLUMNS, EXTENSIONS = add_admin(vars(), "BE", "WAL")

def convert(output_file, cache = None, **kwargs):
    def file_migration(data, path, uri, layer):
        return gml_assure_columns(data, path, uri, layer,
                                  crop_name={"ElementPath": "specificLandUse@title", "Type": "String", "Width": 255},
                                  crop_code={"ElementPath": "specificLandUse@href", "Type": "String", "Width": 255})

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
        column_additions=ADD_COLUMNS,
        column_migrations=COLUMN_MIGRATIONS,
        extensions=EXTENSIONS,
        license=LICENSE,
        layer_filter=lambda layer, uri: layer == LAYER,
        file_migration=file_migration,
        index_as_id=True,
        **kwargs
    )
