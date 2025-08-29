import re
import sys

from loguru import logger

from fiboa_cli.describe import DescribeFiboaFile
from fiboa_cli.fiboa.version import spec_pattern


def test_describe(capsys):
    # todo: use fixture
    logger.remove()
    logger.add(sys.stdout, format="{message}", level="DEBUG", colorize=False)

    describe = DescribeFiboaFile("tests/data-files/fiboa-example.json")
    describe.describe()

    out, err = capsys.readouterr()

    assert "Vecorel Version: 0.1.0" in out
    assert "Fiboa Version: 0.3.0" in out
    # Check that the specification is not in the extension list
    assert not re.search(spec_pattern, out)
