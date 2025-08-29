from pathlib import Path

import pytest
from jsonschema.exceptions import ValidationError
from vecorel_cli.validate import ValidateData


@pytest.mark.parametrize(
    "test",
    [
        ("fiboa-example.json", True),
        (
            "fiboa-invalid.json",
            [
                Exception(
                    "Collection 'de_nrw': Required schema https://fiboa.org/specification/v([^/]+)/schema.yaml not found"
                )
            ],
        ),
    ],
)
def test_validate(test):
    from fiboa_cli import Registry  # noqa

    filename, expected = test
    filepath = Path("./tests/data-files/") / filename

    result = ValidateData().validate(filepath)

    if expected is True:
        assert result.errors == []
        assert result.is_valid()
    else:
        assert isinstance(result.errors, list)
        assert len(result.errors) == len(expected), "More or less errors than expected"
        for idx, error in enumerate(result.errors):
            expect = expected[idx]
            if isinstance(expect, Exception):
                assert isinstance(error, type(expect)), (
                    f"Expected {type(expect)} but got {type(error)}"
                )
                message = error.message if isinstance(error, ValidationError) else str(error)
                if isinstance(expect, ValidationError):
                    assert message == expect.message
                elif isinstance(expect, FileNotFoundError):
                    pass  # ignore exact message for FileNotFoundError
                elif isinstance(expect, Exception):
                    assert message == str(expect)
            else:
                assert error == expect

        assert not result.is_valid()
