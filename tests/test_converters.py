from fiboa_cli import converters
from click.testing import CliRunner


def test_describe():
    runner = CliRunner()
    result = runner.invoke(converters, [])
    assert result.exit_code == 0, result.output
    assert "Short Title" in result.output
    assert "License" in result.output
    assert "be_vlg" in result.output
    assert "Belgium, Flanders" in result.output
    assert "None" not in result.output
