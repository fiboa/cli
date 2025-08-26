import tempfile
from pathlib import Path

import vecorel_cli.vecorel.util as util
from pytest import fixture


@fixture
def tmp_parquet_file():
    # Windows can't properly handle NamedTemporaryFile etc.
    # Let's create a folder instead and then create a file manually.
    with tempfile.TemporaryDirectory() as temp_dir:
        folder = Path(temp_dir)
        file = folder / "test.parquet"

        yield file


@fixture
def tmp_folder():
    # Windows can't properly handle NamedTemporaryFile etc.
    # Let's create a folder instead and then create a file manually.
    with tempfile.TemporaryDirectory(delete=False) as temp_dir:
        folder = Path(temp_dir)
        yield folder


@fixture
def tmp_parquet():
    with tempfile.NamedTemporaryFile(suffix=".parquet") as out:
        yield out


def raiser(message):
    def _method(*args, **kwargs):
        raise Exception(message)

    return _method


@fixture
def block_stream_file():
    # disable stream_file and load_file so we don't accidentally download urls during test
    # tests become flaky if external sources change / are down
    def check_path(uri):
        # only allow schema.{json|yaml}
        assert not (uri.startswith("https://") and "schema." not in uri), (
            f"Should not load external resources during test {uri}"
        )
        return load_file(uri)

    stream_file, load_file = util.stream_file, util.load_file
    util.stream_file = raiser("convert_utils.stream_file() should not be called during test")
    util.load_file = check_path

    yield
    util.stream_file, util.load_file = stream_file, load_file
