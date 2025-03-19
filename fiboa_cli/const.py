LOG_STATUS_COLOR = {"info": "white", "warning": "yellow", "error": "red", "success": "green"}

SUPPORTED_PROTOCOLS = ["http", "https", "s3", "gs"]

STAC_COLLECTION_SCHEMA = (
    "http://schemas.stacspec.org/v{version}/collection-spec/json-schema/collection.json"
)
GEOPARQUET_SCHEMA = "https://geoparquet.org/releases/v{version}/schema.json"
STAC_TABLE_EXTENSION = "https://stac-extensions.github.io/table/v1.2.0/schema.json"

COMPRESSION_METHODS = ["brotli", "gzip", "lz4", "snappy", "zstd", "none"]

CORE_COLUMNS = [
    "id",
    "geometry",
    "area",
    "perimeter",
    "determination_datetime",
    "determination_method",
]
