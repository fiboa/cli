import sys
import time

import click
import pandas as pd

from .cli.util import (
    check_ext_schema_for_cli,
    parse_converter_input_files,
    valid_files_folders_for_cli,
)
from .const import (
    COMPRESSION_METHODS,
)
from .convert import convert as convert_
from .convert import list_all_converter_ids, list_all_converters
from .create_geoparquet import create_geoparquet as create_geoparquet_
from .encoding.geojson import GeoJSON
from .encoding.geoparquet import GeoParquet
from .util import (
    log,
)
from .validate import validate as validate_


## VALIDATE
@click.command()
@click.argument(
    "files",
    nargs=-1,
    callback=lambda ctx, param, value: valid_files_folders_for_cli(
        value, GeoJSON.ext + GeoParquet.ext
    ),
)
@click.option(
    "--data",
    "-d",
    is_flag=True,
    type=click.BOOL,
    help="EXPERIMENTAL: Validate the data in the GeoParquet file. Enabling this might be slow or exceed memory. Default is False.",
    default=False,
)
@click.option(
    "--schemas",
    "-s",
    multiple=True,
    callback=lambda ctx, param, value: check_ext_schema_for_cli(value, allow_none=False),
    help="Maps a remote Vecorel schema URL to a local file. First the URL, then the local file path. Separated with a comma character. Example: https://example.com/schema.yaml,/path/to/schema.yaml",
)
@click.option(
    "--timer",
    is_flag=True,
    type=click.BOOL,
    help="Measure the time the validation took.",
    default=False,
    hidden=True,
)
def validate(files, data, schemas, timer):
    """
    Validates a Vecorel GeoParquet or GeoJSON file.
    """
    start = time.perf_counter()
    log(f"Vecorel CLI {__version__} - Validator\n", "success")
    config = {
        "schemas": schemas,
        "data": data,
    }

    if len(files) == 0:
        log("No files to validate", "error")
        sys.exit(1)

    exit = 0
    for file in files:
        log(f"Validating {file}", "info")
        try:
            start_step = time.perf_counter()
            result = validate_(file, config)
            if result:
                log("\n  => VALID\n", "success")
            else:
                log("\n  => INVALID\n", "error")
                exit = 1
        except Exception as e:
            log(f"\n  => UNKNOWN: {e}\n", "error")
            exit = 2
        finally:
            if timer:
                end_step = time.perf_counter()
                log(f"Validated {file} in {end_step - start_step:0.4f} seconds")

    if timer:
        end = time.perf_counter()
        log(f"All validated in {end - start:0.4f} seconds")

    sys.exit(exit)


## CREATE PARQUET
@click.command()
@click.argument(
    "files",
    nargs=-1,
    callback=lambda ctx, param, value: valid_files_folders_for_cli(value, GeoJSON.ext),
)
@click.option(
    "--out", "-o", type=click.Path(exists=False), help="Path to write the file to.", required=True
)
@click.option(
    "--schemas",
    "-s",
    multiple=True,
    callback=lambda ctx, param, value: check_ext_schema_for_cli(value, allow_none=False),
    help="Maps a remote Vecorel schema URL to a local file. First the URL, then the local file path. Separated with a comma character. Example: https://example.com/schema.yaml,/path/to/schema.yaml",
)
def create_geoparquet(files, out, schemas):
    """
    Create a Vecorel GeoParquet file from Vecorel GeoJSON file(s).
    """
    log(f"Vecorel CLI {__version__} - Create GeoParquet\n", "success")
    config = {
        "files": files,
        "out": out,
        "schemas": schemas,
    }
    try:
        create_geoparquet_(config)
    except Exception as e:
        log(e, "error")
        sys.exit(1)


## CONVERT
@click.command()
@click.argument("dataset", nargs=1, type=click.Choice(list_all_converter_ids()))
@click.option(
    "--out",
    "-o",
    type=click.Path(exists=False),
    help="Path to write the GeoParquet file to.",
    required=True,
)
@click.option(
    "--input",
    "-i",
    type=click.STRING,
    help="File(s) or URL(s) to read from. Can be used multiple times. Specific files from ZIP and 7Z archives can be picked by providing the archive path and the file path in the archive separated by a pipe sign. To pick multiple files from a single archive separate them by comma. Example: /path/to/archive.zip|file1.gpkg,subfolder/file2.gpkg",
    callback=parse_converter_input_files,
    multiple=True,
    default=None,
)
@click.option(
    "--year",
    type=click.INT,
    help="Choose a specific year to read data from. Default is the latest available year.",
)
@click.option(
    "--cache",
    "-c",
    type=click.Path(exists=False),
    help="By default the CLI downloads the source data on every execution. Specify a local folder to avoid downloading the files again. If the files exist, reads from there, otherwise stores the files there.",
    default=None,
)
@click.option(
    "--source-coop",
    "-h",
    type=click.STRING,
    help="(Future) URL to the source cooperative repository, will be added to the Collection metadata.",
    default=None,
)
@click.option(
    "--collection",
    is_flag=True,
    type=click.BOOL,
    help="Export a Collection JSON alongside the data file.",
    default=False,
)
@click.option(
    "--compression",
    "-pc",
    type=click.Choice(COMPRESSION_METHODS),
    help="Compression method for the Parquet file.",
    show_default=True,
    default="brotli",
)
@click.option(
    "--geoparquet1",
    "-gp1",
    is_flag=True,
    type=click.BOOL,
    help="Enforces generating a GeoParquet 1.0 file. Defaults to GeoParquet 1.1 with bounding box.",
    default=False,
)
@click.option(
    "--mapping-file",
    "-m",
    type=click.STRING,
    help="Url of mapping file. Some converters use additional sources with mapping data.",
    default=None,
)
@click.option(
    "--original-geometries",
    "-og",
    is_flag=True,
    type=click.BOOL,
    help="Keep the source geometries as provided, i.e. this option disables that geomtries are made valid and converted to Polygons.",
    default=False,
)
def convert(
    dataset,
    out,
    input,
    year,
    cache,
    source_coop,
    collection,
    compression,
    geoparquet1,
    mapping_file,
    original_geometries,
):
    """
    Converts existing field boundary datasets to Vecorel.
    """
    log(f"Vecorel CLI {__version__} - Convert '{dataset}'\n", "success")
    try:
        convert_(
            dataset,
            out,
            input,
            year,
            cache,
            source_coop,
            collection,
            compression,
            geoparquet1,
            mapping_file,
            original_geometries,
        )
    except Exception as e:
        log(e, "error")
        sys.exit(1)


## CONVERTERS
@click.command()
@click.option(
    "--providers",
    "-p",
    is_flag=True,
    type=click.BOOL,
    help="Show the provider name(s)",
    default=False,
)
@click.option(
    "--sources", "-s", is_flag=True, type=click.BOOL, help="Show the source(s)", default=False
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    type=click.BOOL,
    help="Does not shorten the content of the columns",
    default=False,
)
def converters(providers, sources, verbose):
    """
    Lists all available converters.
    """
    log(f"Vecorel CLI {__version__} - List of Converters\n", "success")

    columns = {"SHORT_NAME": "Short Title", "LICENSE": "License"}
    if providers:
        columns["PROVIDERS"] = "Provider(s)"
    if sources:
        columns["SOURCES"] = "Source(s)"

    keys = list(columns.keys())
    converters = list_all_converters(keys)
    df = pd.DataFrame.from_dict(converters, orient="index", columns=keys)
    df.rename(columns=columns, inplace=True)

    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_colwidth", None if verbose else 35)

    log(df)
