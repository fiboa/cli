from ..convert_utils import convert as convert_

SOURCES = "https://service.pdok.nl/rvo/referentiepercelen/atom/downloads/referentiepercelen.gpkg"

ID = "nl"
SHORT_NAME = "Netherlands"
TITLE = "Field boundaries for The Netherlands"
DESCRIPTION = """
A field block (Dutch: "Referentieperceel"), formerly known as "AAN" (Agrarisch Areaal Nederland),
is a contiguous agricultural area surrounded by permanent boundaries, which is cultivated by one or
more farmers with one or more crops, is fully or partially set aside or is fully or partially
taken out of production.

The following field block types exist:

- Woods (Hout)
- Agricultural area (Landbouwgrond)
- Other (Overig)
- Water (Water)

We filter on "Agricultural area" in this converter.
For crop data, look at BasisRegistratie gewasPercelen (BRP)
"""

PROVIDERS = [
    {
        "name": "RVO / PDOK",
        "url": "https://www.pdok.nl/introductie/-/article/referentiepercelen",
        "roles": ["producer", "licensor"]
    }
]
ATTRIBUTION = None
# Both http://creativecommons.org/publicdomain/zero/1.0/deed.nl and http://creativecommons.org/publicdomain/mark/1.0/
LICENSE = "CC0-1.0"

ADD_COLUMNS = {
    "determination_datetime": "2023-06-15T00:00:00Z"
}

COLUMNS = {
    'geometry': 'geometry',
    'id': 'id',
    'area': "area",
    'versiebron': 'source'
}

COLUMN_FILTERS = {
    # type = "Hout" | "Landbouwgrond" | "Overig" | "Water"
    "type": lambda col: col == "Landbouwgrond"
}

def migrate(gdf):
    # Projection is in CRS 28992 (RD New), this is the area calculation method of the source organization
    gdf['area'] = gdf.area / 10000
    gdf['id'] = gdf.index
    return gdf

MISSING_SCHEMAS = {
    "properties": {
        "source": {
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
        providers=PROVIDERS,
        source_coop_url=source_coop_url,
        missing_schemas=MISSING_SCHEMAS,
        column_additions=ADD_COLUMNS,
        column_filters=COLUMN_FILTERS,
        migration=migrate,
        attribution=ATTRIBUTION,
        store_collection=collection,
        license=LICENSE,
        compression=compression,
        explode_multipolygon=True,
        # fix_as_index allow us to use the fid column
        # see https://github.com/geopandas/geopandas/issues/2794
        fid_as_index=True
    )
