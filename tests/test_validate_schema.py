from fiboa_cli import validate_schema
from click.testing import CliRunner


def test_validate_schema():
    path = f"tests/data-files/inspire-schema.yaml"
    runner = CliRunner()
    result = runner.invoke(validate_schema, [path])
    assert result.exit_code == 0, result.output
    assert "- VALID" in result.output
