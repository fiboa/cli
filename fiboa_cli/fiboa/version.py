from vecorel_cli.vecorel.schemas import CollectionSchemas
from vecorel_cli.vecorel.version import check_versions

supported_fiboa_versions = ">=0.3.0,<0.4.0"
spec_pattern = r"https://fiboa.org/specification/v([^/]+)/schema.yaml"
spec_schema = "https://fiboa.org/specification/v{version}/schema.yaml"


def is_supported(version, raise_exception=False) -> bool:
    result = check_versions(version, supported_fiboa_versions)
    if not result and raise_exception:
        raise ValueError(
            f"Fiboa version {version} is not supported, supported are {supported_fiboa_versions}"
        )
    return result


def get_versions(schema: CollectionSchemas) -> tuple[str, str, str, str, set[str]]:
    vecorel_version, vecorel_uri, vecorel_extensions = schema.get()
    fiboa_version, fiboa_uri, extensions = CollectionSchemas.parse_schemas(
        vecorel_extensions, spec_pattern
    )
    return vecorel_version, vecorel_uri, fiboa_version, fiboa_uri, extensions
