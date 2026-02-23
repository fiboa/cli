from fiboa_cli.conversion.fiboa_converter import FiboaBaseConverter


class RwRwandaConverter(FiboaBaseConverter):
    # Not publicly hosted yet — user must supply via -i flag
    sources = {}
    data_access = """
Request access and download the field boundary parquet from the NASA Harvest
Rwanda Field Boundary Competition dataset on Source Cooperative:

    https://source.coop/nasa/rwanda-field-boundary-competition

Then run the converter with the -i flag pointing to your local copy:

    fiboa convert rw_rwanda -o rw_rwanda.parquet \\
        -i rw_rwanda_2021.parquet=/path/to/boundaries_rwanda_2021.parquet
    """

    id = "rw_rwanda"
    short_name = "Rwanda"
    title = "Rwanda Crop Field Boundaries"
    description = """
Field boundaries for smallholder farms in eastern Rwanda from the NASA Harvest
Rwanda Field Boundary Competition dataset. Annotated from Planet imagery for
the 2021 growing season.
    """
    provider = "NASA Harvest <https://source.coop/nasa/rwanda-field-boundary-competition>"
    attribution = "https://doi.org/10.34911/rdnt.g580ww"
    license = "CC-BY-4.0"

    columns = {
        "geometry": "geometry",
        "id": "id",
        "determination_datetime": "determination:datetime",
    }

    def migrate(self, gdf):
        gdf["id"] = gdf["id"].astype(str)
        return super().migrate(gdf)
