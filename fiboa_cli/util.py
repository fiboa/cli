import json
import os
import re
from typing import Union
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import click
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import referencing
import yaml
from fsspec import AbstractFileSystem
from fsspec.implementations.http import HTTPFileSystem
from fsspec.implementations.local import LocalFileSystem
from geopandas.io.arrow import _arrow_to_geopandas
from jsonschema.validators import Draft7Validator, Draft202012Validator
from pyarrow import NativeFile
from pyarrow.fs import FSSpecHandler, PyFileSystem

from .const import GEOPARQUET_SCHEMA, LOG_STATUS_COLOR, STAC_COLLECTION_SCHEMA, SUPPORTED_PROTOCOLS
from .version import fiboa_version

file_cache = {}


def log(text: str, status="info", nl=True):
    """Log a message with a severity level (which leads to different colors)"""
    click.echo(click.style(text, fg=LOG_STATUS_COLOR[status]), nl=nl)


def load_file(uri):
    """Load files from various sources"""
    if uri in file_cache:
        return file_cache[uri]

    fs = get_fs(uri)

    with fs.open(uri) as f:
        data = f.read()

    if uri.endswith(".yml") or uri.endswith(".yaml"):
        data = yaml.safe_load(data)
    elif uri.endswith(".json") or uri.endswith(".geojson"):
        data = json.loads(data)

    file_cache[uri] = data

    return data


def get_pyarrow_file(uri) -> NativeFile:
    fs = get_fs(uri)
    pyarrow_fs = PyFileSystem(FSSpecHandler(fs))
    return pyarrow_fs.open_input_file(uri)


def load_parquet_schema(uri: Union[str, NativeFile]) -> pq.ParquetSchema:
    """Load schema from Parquet file"""
    if isinstance(uri, str):
        uri = get_pyarrow_file(uri)
    return pq.read_schema(uri)


def load_parquet_metadata(uri: Union[str, NativeFile]) -> pq.FileMetaData:
    """Load metadata from Parquet file"""
    if isinstance(uri, str):
        uri = get_pyarrow_file(uri)
    return pq.read_metadata(uri)


def load_parquet_data(uri: str, nrows=None, columns=None) -> pd.DataFrame:
    """Load data from Parquet file"""
    f = get_pyarrow_file(uri)

    if nrows is None:
        table = pq.read_table(f, columns=columns)
    else:
        pf = pq.ParquetFile(f)
        rows = next(pf.iter_batches(batch_size=nrows, columns=columns))
        table = pa.Table.from_batches([rows])

    if table.schema.metadata is not None and b"geo" in table.schema.metadata:
        return _arrow_to_geopandas(table)
    else:
        return table.to_pandas()


def load_fiboa_schema(config):
    """Load fiboa schema"""
    schema_url = config.get("schema")
    schema_version = config.get("fiboa_version", fiboa_version)
    if not schema_url:
        schema_url = f"https://fiboa.github.io/specification/v{schema_version}/schema.yaml"
    return load_file(schema_url)


def load_datatypes(version):
    # todo: allow to define a seperate schema from a file (as in load_fiboa_schema)
    dt_url = f"https://fiboa.github.io/specification/v{version}/geojson/datatypes.json"
    response = load_file(dt_url)
    return response["$defs"]


def get_fs(url_or_path: str) -> AbstractFileSystem:
    """Choose fsspec filesystem by sniffing input url"""
    parsed = urlparse(url_or_path)

    if parsed.scheme in ("http", "https"):
        if re.search(r"[?&]blocksize=0", url_or_path):
            # We read in chunks. Some origin-server don't support http-range request
            # Add an additional blocksize=0 parameter to your url for a workaround
            return HTTPFileSystem(block_size=0)
        return HTTPFileSystem()

    if parsed.scheme == "s3":
        from s3fs import S3FileSystem

        return S3FileSystem()

    if parsed.scheme == "gs":
        from gcsfs import GCSFileSystem

        return GCSFileSystem()

    return LocalFileSystem()


def is_valid_file_uri(uri, extensions=[]):
    """Determine if the input is a file path or a URL and handle it."""
    if not isinstance(uri, str):
        return None
    elif len(extensions) > 0 and not uri.endswith(tuple(extensions)):
        return None
    elif os.path.exists(uri):
        return uri
    elif is_valid_url(uri):
        return uri
    else:
        raise click.BadParameter(
            "Input must be an existing local file or a URL with protocol: "
            + ",".join(SUPPORTED_PROTOCOLS)
        )


def is_valid_url(url):
    """Check if a URL is valid."""
    try:
        result = urlparse(url)
        return all([result.scheme in SUPPORTED_PROTOCOLS, result.netloc])
    except ValueError:
        return False


def valid_files_folders_for_cli(value, extensions=[]):
    files = []
    for v in value:
        v = is_valid_file_uri(v)
        if os.path.isdir(v):
            for f in os.listdir(v):
                if len(extensions) > 0 and not f.endswith(tuple(extensions)):
                    continue
                if f == "collection.json" or f == "catalog.json":  # likely STAC
                    continue
                files.append(os.path.join(v, f))
        else:
            files.append(v)
    return files


def valid_file_for_cli(ctx, param, value):
    return is_valid_file_uri(value)


def valid_file_for_cli_with_ext(value, extensions):
    return is_valid_file_uri(value, extensions)


def valid_folder_for_cli(ctx, param, value):
    """Determine if the input is a folder."""
    if os.path.exists(value) and os.path.isdir(value):
        return value
    else:
        raise click.BadParameter("Input must be an existing local folder")


def get_collection(data, collection_path=None, basepath=None):
    # If the user provided a collection, enforce using it
    if collection_path is not None:
        return load_file(collection_path)

    # Look if the data contains a fiboa property
    if "fiboa" in data:
        return data.get("fiboa")

    # Look for a collection link in the data and load the collection from there
    links = data.get("links", [])
    for link in links:
        media_type = link.get("type")
        if link.get("rel") == "collection" and (
            media_type is None or media_type == "application/json"
        ):
            href = link.get("href")
            if basepath is not None:
                href = os.path.join(os.path.dirname(basepath), href)
            return load_file(href)

    # No collection found
    return None


def parse_converter_input_files(ctx, param, value):
    if value is None:
        return None
    elif not isinstance(value, tuple):
        raise click.BadParameter("Input files must be a tuple")
    elif len(value) == 0:
        return None

    sources = {}
    for v in value:
        if "|" not in v:
            sources[v] = name_from_uri(v)
        else:
            uri, archive = v.split("|", 2)
            files = archive.split(",")
            sources[uri] = files

    return sources


def parse_map(value, separator="="):
    if value is None:
        return {}
    elif not isinstance(value, tuple):
        raise click.BadParameter("Input files must be a tuple")
    elif len(value) == 0:
        return {}

    mapping = {}
    for v in value:
        key, value = v.split(separator, 2)
        mapping[key] = value

    return mapping


def name_from_uri(url):
    if "://" in url:
        try:
            url = urlparse(url).path
        except ValueError:
            pass
    return os.path.basename(url)


def check_ext_schema_for_cli(value, allow_none=False):
    map_ = {}
    for v in value:
        try:
            part = v.split(",", 2)
            map_[part[0]] = None if len(part) < 2 and allow_none else part[1]
        except IndexError:
            optionally = "optionally " if allow_none else ""
            raise click.BadParameter(
                f"Extension schema must be a URL and {optionally}a local file path separated by a comma character"
            )

    return map_


def is_schema_empty(schema):
    return len(schema.get("properties", {})) == 0 and len(schema.get("required", {})) == 0


def merge_schemas(*schemas):
    """Merge multiple schemas into one"""
    result = {"required": [], "properties": {}}
    for schema in schemas:
        schema = migrate_schema(schema)
        result["required"] += schema.get("required", [])
        result["properties"].update(schema.get("properties", {}))

    return result


def pick_schemas(schema, property_names, rename={}):
    """Pick and rename schemas for specific properties"""
    result = {"required": [], "properties": {}}
    required = schema.get("required", [])
    properties = schema.get("properties", {})
    for prop in property_names:
        prop2 = rename[prop] if prop in rename else prop
        if prop in required:
            result["required"].append(prop2)
        if prop in properties:
            result["properties"][prop2] = properties[prop]

    return result


def migrate_schema(schema):
    """Migrate schema to a new version"""
    return schema.copy()


def parse_metadata(schema, key):
    if key in schema.metadata:
        return json.loads(schema.metadata[key].decode("utf-8"))
    else:
        str_key = key.decode("utf-8")
        log(f"Parquet file schema does not have a '{str_key}' key", "warning")
        return None


def to_iso8601(dt):
    iso = dt.isoformat()
    if iso.endswith("+00:00"):
        return iso[:-6] + "Z"
    elif re.search(r"[+-]\d{2}:\d{2}$", iso):
        raise ValueError("Timezone offset is not supported")
    else:
        return iso + "Z"


def load_collection_schema(obj):
    if "stac_version" in obj:
        return load_file(STAC_COLLECTION_SCHEMA.format(version=obj["stac_version"]))
    else:
        return None


def load_geoparquet_schema(obj):
    if "version" in obj:
        return load_file(GEOPARQUET_SCHEMA.format(version=obj["version"]))
    else:
        return None


def log_extensions(collection, logger):
    extensions = collection.get("fiboa_extensions", [])
    if len(extensions) == 0:
        logger("fiboa extensions: none")
    else:
        logger("fiboa extensions:")
        for extension in extensions:
            logger(f"  - {extension}")


def create_validator(schema):
    if schema["$schema"] == "http://json-schema.org/draft-07/schema#":
        instance = Draft7Validator
    else:
        instance = Draft202012Validator

    return instance(
        schema,
        format_checker=instance.FORMAT_CHECKER,
        registry=referencing.Registry(retrieve=retrieve_remote_schema),
    )


def retrieve_remote_schema(uri: str):
    request = Request(uri)
    with urlopen(request) as response:
        return referencing.Resource.from_contents(
            json.load(response),
            default_specification=referencing.jsonschema.DRAFT202012,
        )
