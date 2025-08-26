from vecorel_cli.converters import Converters


def test_describe(capsys):
    from fiboa_cli import Registry  # noqa

    Converters().converters()
    out, err = capsys.readouterr()
    output = out + err

    assert "Short Title" in output
    assert "License" in output
    assert "at" in output
    assert "Austria" in output
    # assert "None" not in output
