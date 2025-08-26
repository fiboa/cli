from click.testing import CliRunner
from vecorel_cli.converters import Converters


def test_describe():
    runner = CliRunner()
    result = runner.invoke(Converters.get_cli_command(Converters), [])
    assert result.exit_code == 0, result.output
    assert "Short Title" in result.output
    assert "License" in result.output
    assert "at" in result.output
    assert "Austria" in result.output
    # assert "None" not in result.output
