from fiboa_cli.jsonschema import jsonschema
from fiboa_cli.util import load_file
from fiboa_cli.version import fiboa_version


def test_conversion():
    config = {
        "schema": "tests/data-files/jsonschema/test1.yaml",
        "fiboa_version": fiboa_version,
        "id": "https://example.com/schema.json",
    }
    created_json_schema = jsonschema(config)

    expected_json_schema = load_file("tests/data-files/jsonschema/test1.json")
    assert created_json_schema == expected_json_schema
