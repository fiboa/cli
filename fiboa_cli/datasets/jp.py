from fiboa_cli.conversion.duckdb import FiboaDuckDBBaseConverter


class JPConverter(FiboaDuckDBBaseConverter):
    variants = {
        "test": "./tests/data-files/convert/jp/jp_field_polygons_2024.parquet",
        "2024": "https://data.source.coop/pacificspatial/field-polygon-jp/parquet/jp_field_polygons_2024.parquet",
        "2023": "https://data.source.coop/pacificspatial/field-polygon-jp/parquet/jp_field_polygons_2023.parquet",
        "2022": "https://data.source.coop/pacificspatial/field-polygon-jp/parquet/jp_field_polygons_2022.parquet",
        "2021": "https://data.source.coop/pacificspatial/field-polygon-jp/parquet/jp_field_polygons_2021.parquet",
    }

    id = "jp"
    short_name = "Japan"
    title = "Japan Fude Parcels"
    description = """
Japanese Farmland Parcel Polygons (Fude Polygons in Japanese) represent parcel information of farmland.
The polygons are manually digitized data derived from aerial imagery, such as satellite images. Since no
on-site verification or similar procedures have been conducted, the data may not necessarily match the actual
current conditions. Fude Polygons are created for the purpose of roughly indicating the locations of farmland.
    """

    provider = "Japanese Ministry of Agriculture, Forestry and Fisheries (MAFF, 農林水産省) <https://www.maff.go.jp/>"
    attribution = "Fude Polygon Data (2021-2024). Japanese Ministry of Agriculture, Forestry and Fisheries. Processed by Pacific Spatial Solutions, Inc"
    license = "CC-BY-4.0"

    columns = {
        "GEOM": "geometry",
        "polygon_uuid": "id",
        "land_type_en": "land_type_en",
        "local_government_cd": "admin_local_code",
    }
    column_additions = {"determination:datetime": "2024-01-01T00:00:00Z"}
    missing_schemas = {
        "properties": {
            "land_type_en": {"type": "string"},
            "admin_local_code": {"type": "string"},
        }
    }
