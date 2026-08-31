"""Smoke tests for the one-line command wrapper modules: they must import and
expose a command class the registry can register."""

import importlib

import pytest

from fiboa_cli import Registry  # noqa: F401


@pytest.mark.parametrize(
    "module,cls",
    [
        ("fiboa_cli.create_geojson", "CreateGeoJson"),
        ("fiboa_cli.create_geoparquet", "CreateGeoParquet"),
        ("fiboa_cli.create_jsonschema", "CreateJsonSchema"),
        ("fiboa_cli.merge", "MergeDatasets"),
        ("fiboa_cli.validate_schema", "ValidateSchema"),
        ("fiboa_cli.rename_extension", "RenameExtension"),
    ],
)
def test_command_module_exposes_class(module, cls):
    mod = importlib.import_module(module)
    assert hasattr(mod, cls), f"{module} does not define {cls}"


def test_registry_registers_fiboa_commands():
    from vecorel_cli.registry import Registry as R

    R.instance.register_commands()
    names = {getattr(c, "__name__", str(c)) for c in R.instance.commands}
    assert {"publish", "improve", "create-stac-collection", "merge"} <= names
