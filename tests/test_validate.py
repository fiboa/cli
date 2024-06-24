from fiboa_cli import validate
from click.testing import CliRunner


def test_validate():
    path = f"tests/data-files/inspire.parquet"
    runner = CliRunner()
    result = runner.invoke(validate, [path, '--data'])
    assert result.exit_code == 0, result.output
    assert "Validating tests/data-files/inspire.parquet" in result.output
    assert "- https://fiboa.github.io/inspire-extension/v0.2.0/schema.yaml" in result.output
    assert "Data was not validated" not in result.output
    assert "=> VALID" in result.output
