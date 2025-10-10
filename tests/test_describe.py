import re
import sys

from loguru import logger
from vecorel_cli.vecorel.version import vecorel_version

from fiboa_cli.describe import DescribeFiboaFile
from fiboa_cli.fiboa.version import fiboa_version, spec_pattern


def test_describe(capsys):
    # todo: use fixture
    logger.remove()
    logger.add(sys.stdout, format="{message}", level="DEBUG", colorize=False)

    describe = DescribeFiboaFile("tests/data-files/fiboa-example.json")
    describe.describe()

    out, err = capsys.readouterr()

    assert f"Vecorel Version: {vecorel_version}" in out
    assert f"Fiboa Version: {fiboa_version}" in out
    # Check that the specification is not in the extension list
    assert not re.search(spec_pattern, out)
