import os
import tempfile
from fiboa_cli import create_geoparquet, validate
from pytest import fixture
from click.testing import CliRunner
from fiboa_cli.util import load_parquet_data

@fixture
def out_file():
    with tempfile.NamedTemporaryFile() as out:
        yield out.name

def test_create_geoparquet(out_file):
    path = f"tests/data-files/inspire.json"
    runner = CliRunner()
    result = runner.invoke(create_geoparquet, [path, '-o', out_file])
    assert result.exit_code == 0, result.output
    assert f"Wrote to {out_file}" in result.output

    assert os.path.exists(out_file)
    result = runner.invoke(validate, [out_file, '--data'])
    assert result.exit_code == 0, result.output

    data = load_parquet_data(out_file)
    assert len(data) == 1
