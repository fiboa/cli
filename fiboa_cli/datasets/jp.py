import pandas as pd

from ..convert_utils import BaseConverter


class JPConverter(BaseConverter):
    years = {
        2024: "https://data.source.coop/pacificspatial/field-polygon-jp/parquet/jp_field_polygons_2024.parquet",
        2023: "https://data.source.coop/pacificspatial/field-polygon-jp/parquet/jp_field_polygons_2023.parquet",
        2022: "https://data.source.coop/pacificspatial/field-polygon-jp/parquet/jp_field_polygons_2022.parquet",
        2021: "https://data.source.coop/pacificspatial/field-polygon-jp/parquet/jp_field_polygons_2021.parquet",
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

    providers = [
        {
            "name": "Japanese Ministry of Agriculture, Forestry and Fisheries (MAFF, 農林水産省)",
            "url": "https://www.maff.go.jp/",
            "roles": ["licensor", "producer"],
        },
        {
            "name": "Hiroo Imaki, Pacific Spatial Solutions",
            "url": "https://pacificspatial.com/",
            "roles": ["processor"],
        },
    ]
    attribution = "Fude Polygon Data (2021-2024). Japanese Ministry of Agriculture, Forestry and Fisheries. Processed by Pacific Spatial Solutions, Inc"
    license = "CC-BY-4.0"

    columns = {
        "GEOM": "geometry",
        "polygon_uuid": "id",
        "land_type_en": "land_type_en",
        "local_government_cd": "admin_local_code",
        "issue_year": "determination_datetime",
    }
    column_migrations = {
        "issue_year": lambda col: pd.to_datetime(col, format="%Y"),
    }

    missing_schemas = {
        "properties": {
            "land_type_en": {"type": "string"},
            "admin_local_code": {"type": "string"},
        }
    }

    def convert(self, *args, **kwargs):
        # Open only these columns to limit memory usage
        super().convert(
            *args,
            columns=["GEOM", "polygon_uuid", "land_type_en", "local_government_cd", "issue_year"],
            **kwargs,
        )
