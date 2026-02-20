from fiboa_cli.conversion.fiboa_converter import FiboaBaseConverter


CROP_EXTENSION = "https://fiboa.org/crop-extension/v0.2.0/schema.yaml"


class DeFusionConverter(FiboaBaseConverter):
    sources = {
        "https://data.source.coop/esa/fusion-competition/br-17E-243N-crop-labels-test-2019.geojson": "de_test_2019.geojson",
        "https://data.source.coop/esa/fusion-competition/br-18E-242N-crop-labels-train-2018.geojson": "de_train_2018.geojson",
    }
    id = "de_fusion"
    short_name = "Germany (Fusion)"
    title = "Germany Crop Field Boundaries (Fusion Competition)"
    description = """
Field boundaries for Germany from the ESA Fusion Competition dataset.
Contains crop field polygons labeled with crop type information,
covering two tiles in the Brandenburg region of Germany.
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
        "determination:datetime": "2019-01-01T00:00:00Z",
    }

    def _normalize_geojson_properties(self, feature):
        # These GeoJSON files have no top-level feature id, only fid inside properties.
        # Override to use fid so vecorel does not crash looking for feature["id"].
        if "id" not in feature["properties"]:
            feature["properties"]["id"] = feature["properties"].get("fid", None)
        return feature

    def migrate(self, gdf):
        return super().migrate(gdf)
