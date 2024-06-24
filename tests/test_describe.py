from fiboa_cli import describe
from click.testing import CliRunner


def test_describe():
    path = f"tests/data-files/inspire.parquet"
    runner = CliRunner()
    result = runner.invoke(describe, [path])
    assert result.exit_code == 0, result.output
    assert "Geometry columns: geometry" in result.output
    assert "- https://fiboa.github.io/inspire-extension/v0.2.0/schema.yaml" in result.output
    assert "== SCHEMA (columns: 4) ==" in result.output
    assert "determination_datetime: timestamp[ms, tz=UTC]" in result.output
    assert "geometry: binary not null" in result.output
    assert "id: string not null" in result.output
    assert "inspire:id: string not null" in result.output
    assert "DATA (rows: 1, groups: 1)" in result.output
