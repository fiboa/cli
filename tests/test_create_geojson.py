import os
import tempfile
from fiboa_cli import create_geojson, validate
from pytest import fixture
from click.testing import CliRunner
from fiboa_cli.util import load_file

@fixture
def out_folder():
    with tempfile.TemporaryDirectory() as out:
        yield out

def test_create_geojson(out_folder):
    path = f"tests/data-files/inspire.parquet"
    runner = CliRunner()
    result = runner.invoke(create_geojson, [path, '-o', out_folder, '-f'])
    assert result.exit_code == 0, result.output
    assert "Found 1 feature" in result.output
    assert "Files written to" in result.output

    out_file = os.path.join(out_folder, "6467974.json")
    assert os.path.exists(out_file)
    geojson = load_file(out_file)
    assert geojson["id"] == "6467974"
    assert geojson["type"] == "Feature"
    assert geojson["properties"]["determination_datetime"] == "2020-01-01T00:00:00Z"
    assert geojson["properties"]["inspire:id"] == "https://geodaten.nrw.de/id/inspire-lc-dgl/landcoverunit/6467974"
    assert geojson["geometry"]["type"] == "Polygon"

    result = runner.invoke(validate, [out_file, '--data'])
    assert result.exit_code == 0, result.output
