import re

from vecorel_cli.registry import Registry, VecorelRegistry

from fiboa_cli.fiboa.version import get_fiboa_uri, spec_pattern


class FiboaRegistry(VecorelRegistry):
    name: str = "fiboa-cli"
    project: str = "fiboa"
    cli_title: str = "fiboa CLI"
    src_package: str = "fiboa_cli"
    core_properties = [
        "id",
        "geometry",
        "collection",
        "metrics:area",
        "metrics:perimeter",
        "category",
        "determination:datetime",
        "determination:method",
        "determination:details",
    ]
    required_extensions = [re.compile(spec_pattern)]
    ignored_datasets = VecorelRegistry.ignored_datasets + ["es.py"]

    def register_commands(self):
        from .convert import ConvertData
        from .converters import Converters
        from .create_geojson import CreateGeoJson
        from .create_geoparquet import CreateGeoParquet
        from .create_jsonschema import CreateJsonSchema
        from .create_stac import CreateStacCollection
        from .describe import DescribeFile
        from .improve import ImproveData
        from .merge import MergeDatasets
        from .publish import Publish
        from .rename_extension import RenameExtension
        from .validate import ValidateData
        from .validate_schema import ValidateSchema

        commands = [
            ConvertData,
            Converters,
            CreateGeoJson,
            CreateGeoParquet,
            CreateJsonSchema,
            CreateStacCollection,
            DescribeFile,
            ImproveData,
            MergeDatasets,
            Publish,
            RenameExtension,
            ValidateData,
            ValidateSchema,
        ]

        for command in commands:
            self.set_command(command)

    def get_default_collection(self, id: str, extensions: set | list | None = None) -> dict:
        extensions = {get_fiboa_uri()} | set(extensions)
        return super().get_default_collection(id, extensions=extensions)


Registry.instance = FiboaRegistry()
