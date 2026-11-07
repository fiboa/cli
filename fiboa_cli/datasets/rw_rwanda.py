from fiboa_cli.conversion.fiboa_converter import FiboaBaseConverter


class RwRwandaConverter(FiboaBaseConverter):
    # NASA Harvest publishes the labels as rasters; Kerner Lab converted them for Fields of the
    # World and publishes the polygons openly
    sources = {
        "https://data.source.coop/kerner-lab/fields-of-the-world-rwanda/boundaries_rwanda_2021.parquet": "rw_rwanda_2021.parquet"
    }

    id = "rw_rwanda"
    short_name = "Rwanda"
    title = "Rwanda Crop Field Boundaries"
    description = """
Field boundaries for smallholder farms in eastern Rwanda from the NASA Harvest
Rwanda Field Boundary Competition dataset. Annotated from Planet imagery for
the 2021 growing season. The competition publishes the labels as rasters; these are the
polygons Kerner Lab (Arizona State University) converted from them for Fields of the World.
    """
    provider = "NASA Harvest <https://source.coop/nasa/rwanda-field-boundary-competition>"
    attribution = "https://doi.org/10.34911/rdnt.g580ww"
    license = "CC-BY-4.0"

    columns = {
        "geometry": "geometry",
        "id": "id",
        "determination_datetime": "determination:datetime",
    }

    column_migrations = {
        "id": lambda col: col.astype(str),
    }
