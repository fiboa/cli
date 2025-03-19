from ..convert_utils import convert as convert_

SOURCES = {
    # Cambodia
    "https://phys-techsciences.datastations.nl/api/access/datafile/100634?gbrecs=true": "2_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100282?gbrecs=true": "3_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100392?gbrecs=true": "4_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100252?gbrecs=true": "5_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100072?gbrecs=true": "6_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100169?gbrecs=true": "7_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100348?gbrecs=true": "8_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100487?gbrecs=true": "9_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100084?gbrecs=true": "10_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100155?gbrecs=true": "11_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100475?gbrecs=true": "12_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100372?gbrecs=true": "13_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100196?gbrecs=true": "14_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100006?gbrecs=true": "15_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100248?gbrecs=true": "16_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100397?gbrecs=true": "17_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100217?gbrecs=true": "18_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100652?gbrecs=true": "19_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100326?gbrecs=true": "20_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100625?gbrecs=true": "21_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100413?gbrecs=true": "33_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100593?gbrecs=true": "34_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100057?gbrecs=true": "35_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100536?gbrecs=true": "36_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100343?gbrecs=true": "37_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100711?gbrecs=true": "38_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100313?gbrecs=true": "39_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100679?gbrecs=true": "57_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100191?gbrecs=true": "58_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100023?gbrecs=true": "59_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100025?gbrecs=true": "60_cambodia_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100543?gbrecs=true": "61_cambodia_areas.gpkg",
    # Vietnam
    "https://phys-techsciences.datastations.nl/api/access/datafile/100297?gbrecs=true": "0_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100636?gbrecs=true": "1_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100574?gbrecs=true": "22_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100095?gbrecs=true": "23_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100398?gbrecs=true": "24_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100187?gbrecs=true": "25_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100065?gbrecs=true": "26_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100425?gbrecs=true": "27_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100589?gbrecs=true": "28_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100021?gbrecs=true": "29_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100043?gbrecs=true": "30_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100562?gbrecs=true": "31_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100437?gbrecs=true": "32_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100549?gbrecs=true": "40_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100039?gbrecs=true": "41_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100427?gbrecs=true": "42_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100466?gbrecs=true": "43_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100014?gbrecs=true": "44_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100464?gbrecs=true": "45_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100416?gbrecs=true": "46_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100115?gbrecs=true": "47_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100510?gbrecs=true": "48_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100459?gbrecs=true": "49_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100340?gbrecs=true": "50_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100119?gbrecs=true": "51_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100086?gbrecs=true": "52_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100467?gbrecs=true": "53_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100176?gbrecs=true": "54_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100145?gbrecs=true": "55_vietnam_areas.gpkg",
    "https://phys-techsciences.datastations.nl/api/access/datafile/100492?gbrecs=true": "56_vietnam_areas.gpkg",
}

ID = "ai4sf"
SHORT_NAME = "Cambodia/Vietnam (AI4SmallFarms)"
TITLE = "Field boundaries for Cambodia and Vietnam (AI4SmallFarms)"
# from https://research.tudelft.nl/en/publications/ai4smallfarms-a-dataset-for-crop-field-delineation-in-southeast-a
DESCRIPTION = """
Agricultural field polygons within smallholder farming systems are essential to facilitate the collection of geo-spatial data useful for farmers, managers, and policymakers.
However, the limited availability of training labels poses a challenge in developing supervised methods to accurately delineate field boundaries using Earth Observation (EO) data.
This data set allows researchers to test and benchmark machine learning methods to delineate agricultural field boundaries in polygon format.
The large-scale data set consists of 439,001 field polygons divided into 62 tiles of approximately 5×5 km distributed across Vietnam and Cambodia, covering a range of fields and diverse landscape types.
The field polygons have been meticulously digitized from satellite images, following a rigorous multi-step quality control process and topological consistency checks.
Multi-temporal composites of Sentinel-2 (S2) images are provided to ensure cloud-free data.
"""

PROVIDERS = [
    {
        "name": "DATA Archiving and Networked Services (DANS)",
        "url": "https://research.tudelft.nl/en/publications/ai4smallfarms-a-dataset-for-crop-field-delineation-in-southeast-a",
        "roles": ["producer", "licensor"],
    }
]
ATTRIBUTION = "Persello, C., Grift, J., Fan, X., Paris, C., Hansch, R., Koeva, M., & Nelson, A. (2023). AI4SmallFarms: A Dataset for Crop Field Delineation in Southeast Asian Smallholder Farms. IEEE Geoscience and Remote Sensing Letters, 20, 1-5. Article 2505705. https://doi.org/10.1109/LGRS.2023.3323095"
LICENSE = "CC-BY-4.0"

COLUMNS = {
    "fiboa_id": "id",
    "id": "group",
    "_predicate": "_predicate",
    "country": "admin:country_code",
    "geometry": "geometry",
}

EXTENSIONS = {"https://fiboa.github.io/administrative-division-extension/v0.1.0/schema.yaml"}

COLUMN_MIGRATIONS = {"country": lambda col: col.map({"cambodia": "KH", "vietnam": "VN"})}

# Add columns with constant values.
# The key is the column name, the value is a constant value that's used for all rows.
ADD_COLUMNS = {
    "determination_datetime": "2021-08-01T00:00:00Z",
    "determination_method": "auto-imagery",
}


def migrate(gdf):
    # Create unique IDs from the dataset in the form "xx_xxxxx"
    gdf["fiboa_id"] = gdf["id"].astype(str).str.zfill(2) + "_" + gdf.index.astype(str).str.zfill(5)
    return gdf


MIGRATION = migrate

MISSING_SCHEMAS = {
    "properties": {
        "group": {"type": "uint8"},
        "group_id": {"type": "uint16"},
        "_predicate": {"type": "string", "enum": ["INTERSECTS"]},
    }
}


# Conversion function, usually no changes required
def convert(output_file, cache=None, **kwargs):
    convert_(
        output_file,
        cache,
        SOURCES,
        COLUMNS,
        ID,
        TITLE,
        DESCRIPTION,
        missing_schemas=MISSING_SCHEMAS,
        extensions=EXTENSIONS,
        column_migrations=COLUMN_MIGRATIONS,
        column_additions=ADD_COLUMNS,
        migration=MIGRATION,
        attribution=ATTRIBUTION,
        license=LICENSE,
        **kwargs,
    )
