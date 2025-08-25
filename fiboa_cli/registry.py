from vecorel_cli.registry import VecorelRegistry, Registry

class FiboaRegistry(VecorelRegistry):
    """
    The public package name of the library (e.g. on pypi).
    """
    name: str = "fiboa-cli"

    """
    The displayable title of the CLI.
    """
    cli_title: str = "fiboa CLI"

    """
    The internal package name of the CLI.
    This is the name of the folder in which the source files are located.
    """
    src_package: str = "fiboa_cli"

    # todo: in fiboa CLI add "area", "perimeter", "determination_datetime", "determination_method"
    core_properties = [
        "id",
        "geometry",
        "collection",
    ]

    # The filenames for datasets (converters) that should be ignored by the CLI.
    # Always ignores files with a starting "." or "__"
    ignored_datasets = [
        "template.py",
    ]

    def get_commands(self):
        """
        The commands that are made available by the CLI.
        """
        from vecorel_cli.convert import ConvertData
        from vecorel_cli.converters import Converters
        from vecorel_cli.create_geojson import CreateGeoJson
        from vecorel_cli.create_geoparquet import CreateGeoParquet
        from vecorel_cli.create_jsonschema import CreateJsonSchema
        from vecorel_cli.create_stac import CreateStacCollection
        from vecorel_cli.describe import DescribeFile
        from vecorel_cli.improve import ImproveData
        from vecorel_cli.merge import MergeDatasets
        from vecorel_cli.rename_extension import RenameExtension
        from vecorel_cli.validate import ValidateData
        from vecorel_cli.validate_schema import ValidateSchema

        return [
            ConvertData,
            Converters,
            CreateGeoJson,
            CreateGeoParquet,
            CreateJsonSchema,
            CreateStacCollection,
            DescribeFile,
            ImproveData,
            MergeDatasets,
            RenameExtension,
            ValidateData,
            ValidateSchema,
        ]

Registry.instance = FiboaRegistry()
