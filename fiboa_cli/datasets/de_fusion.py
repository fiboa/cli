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
        "determination:datetime": "determination:datetime",
    }

    def _normalize_geojson_properties(self, feature):
        # These GeoJSON files have no top-level feature id, only fid inside properties.
        # Override to use fid so vecorel does not crash looking for feature["id"].
        fid = feature["properties"].get("fid")
        if fid is None:
            raise ValueError(f"Feature has no 'fid' property: {feature}")
        feature["properties"]["id"] = fid
        return feature

    def file_migration(self, gdf, path, uri, layer=None):
        # Train file covers 2018, test file covers 2019.
        year = "2018" if "2018" in path else "2019"
        gdf["determination:datetime"] = f"{year}-01-01T00:00:00Z"
        return super().file_migration(gdf, path, uri, layer)

    def migrate(self, gdf):
        # Source GeoJSON uses EPSG:25833 (ETRS89/UTM zone 33N) but the CRS tag
        # is not picked up by the reader, so coordinates arrive labeled as 4326.
        gdf = gdf.set_crs("EPSG:25833", allow_override=True).to_crs("EPSG:4326")
        return super().migrate(gdf)
