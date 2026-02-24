from fiboa_cli.conversion.fiboa_converter import FiboaBaseConverter


CROP_EXTENSION = "https://fiboa.org/crop-extension/v0.2.0/schema.yaml"


class ZaFusionConverter(FiboaBaseConverter):
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
    provider = "ESA Fusion Competition via Source Cooperative <https://source.coop/esa/fusion-competition>"
    attribution = "https://data.source.coop/esa/fusion-competition"
    license = "CC-BY-4.0"
    extensions = {CROP_EXTENSION}
    area_is_in_ha = False
    columns = {
        "geometry": "geometry",
        "id": "id",
        "SHAPE_AREA": "metrics:area",
        "crop_id": "crop:code",
        "crop_name": "crop:name",
    }
    column_additions = {
        "determination:datetime": "2017-01-01T00:00:00Z",
    }

    def _normalize_geojson_properties(self, feature):
        if "id" not in feature["properties"]:
            feature["properties"]["id"] = feature["properties"].get("fid", None)
        return feature

    def migrate(self, gdf):
        return super().migrate(gdf)
