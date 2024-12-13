import tempfile
from pytest import fixture

from fiboa_cli import convert_utils, util


@fixture
def tmp_file():
    with tempfile.NamedTemporaryFile() as out:
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
        assert not (uri.startswith("https://") and not 'schema.' in uri), \
            f"Should not load external resources during test {uri}"
        return load_file(uri)

    stream_file, load_file = convert_utils.stream_file, util.load_file
    convert_utils.stream_file = raiser("convert_utils.stream_file() should not be called during test")
    util.load_file = check_path

    yield
    convert_utils.stream_file, util.load_file = stream_file, load_file
