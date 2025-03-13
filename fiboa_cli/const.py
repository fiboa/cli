LOG_STATUS_COLOR = {"info": "white", "warning": "yellow", "error": "red", "success": "green"}

SUPPORTED_PROTOCOLS = ["http", "https", "s3", "gs"]

FIBOA_SPECIFICAION_PATTERN = r"https://fiboa.github.io/specification/v([^/]+)/schema.yaml"
FIBOA_SPECIFICAION_SCHEMA = "https://fiboa.github.io/specification/v{version}/schema.yaml"
FIBOA_GEOJSON_DATATYPES_SCHEMA = (
    "https://fiboa.github.io/specification/v{version}/geojson/datatypes.json"
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
