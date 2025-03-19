from click.testing import CliRunner

from fiboa_cli import validate_schema


def test_validate_schema():
    path = "tests/data-files/inspire-schema.yaml"
    runner = CliRunner()
    result = runner.invoke(validate_schema, [path])
    assert result.exit_code == 0, result.output
    assert "- VALID" in result.output
