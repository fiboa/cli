import re
import sys

from loguru import logger
from pytest import mark
from vecorel_cli.convert import ConvertData
from vecorel_cli.validate import ValidateData

"""
Create input files with: `ogr2ogr output.gpkg -limit 100 input.gpkg`
Optionally use `-lco ENCODING=UTF-8` if you have character encoding issues.
"""

tests = [
    "at",
]
test_path = "tests/data-files/convert"
extra_convert_parameters = {}


@mark.parametrize("converter", tests)
def test_converter(capsys, tmp_parquet, converter, block_stream_file):
    from fiboa_cli import Registry  # noqa

    logger.remove()
    logger.add(sys.stdout, format="{message}", level="DEBUG", colorize=False)

    path = f"tests/data-files/convert/{converter}"
    # kwargs = extra_convert_parameters.get(converter, {})
    kwargs = {}

    ConvertData(converter).convert(target=tmp_parquet.name, cache=path, **kwargs)
    out, err = capsys.readouterr()
    output = out + err

    error = re.search("Skipped - |No schema defined", output)
    if error:
        raise AssertionError(f"Found error in output: '{error.group(0)}'\n\n{output}")

    ValidateData().validate(tmp_parquet.name)
