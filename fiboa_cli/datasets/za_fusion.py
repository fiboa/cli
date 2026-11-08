from fiboa_cli.conversion.fiboa_converter import FiboaBaseConverter

from .commons.hcat import AddHCATMixin


class ZaFusionConverter(AddHCATMixin, FiboaBaseConverter):
    sources = {
        "https://data.source.coop/esa/fusion-competition/sa-19E-258N-crop-labels-train-2017.geojson": "za_train_258N.geojson",
        "https://data.source.coop/esa/fusion-competition/sa-19E-259N-crop-labels-train-2017.geojson": "za_train_259N.geojson",
        "https://data.source.coop/esa/fusion-competition/sa-20E-259N-crop-labels-test-2017.geojson": "za_test_2017.geojson",
    }
    id = "za_fusion"
    short_name = "South Africa (Fusion)"
    title = "South Africa Crop Field Boundaries (Fusion Competition)"
    description = """
Field boundaries for South Africa from the ESA Fusion Competition dataset.
Contains crop field polygons labeled with crop type information,
covering three tiles in the Western Cape region of South Africa.
    """
    provider = (
        "ESA Fusion Competition via Source Cooperative <https://source.coop/esa/fusion-competition>"
    )
    attribution = "https://data.source.coop/esa/fusion-competition"
    license = "CC-BY-4.0"
    # the five classes of the competition, with their names; crop:code_list points here
    hcat_mapping_csv = "https://fiboa.org/code/za/fusion/crop.csv"
    area_is_in_ha = False
    columns = {
        "geometry": "geometry",
        "fid": "id",
        "SHAPE_AREA": "metrics:area",
        "crop_id": "crop:code",
        "crop_name": "crop:name",
    }
    column_additions = {
        "determination:datetime": "2017-01-01T00:00:00Z",
    }

    def migrate(self, gdf):
        # Source GeoJSON uses EPSG:32734 (WGS84/UTM zone 34S) but the CRS tag
        # is not picked up by the reader, so coordinates arrive labeled as 4326.
        gdf = gdf.set_crs("EPSG:32734", allow_override=True).to_crs("EPSG:4326")
        return super().migrate(gdf)
