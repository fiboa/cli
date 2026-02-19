from fiboa_cli.conversion.fiboa_converter import FiboaBaseConverter


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
    missing_schemas = {
        "properties": {
            "crop:code": {"type": "uint16"},
            "crop:name": {"type": "string"},
        }
    }

    def _normalize_geojson_properties(self, feature):
        # These GeoJSON files have no top-level feature id, only fid inside properties.
        if "id" not in feature["properties"]:
            feature["properties"]["id"] = feature["properties"].get("fid", None)
        return feature

    def migrate(self, gdf):
        # Reproject from EPSG:32734 to WGS84 as required by fiboa spec
        if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs("EPSG:4326")

        # Convert area from m² to hectares
        gdf["SHAPE_AREA"] = gdf["SHAPE_AREA"] / 10000

        return super().migrate(gdf)
