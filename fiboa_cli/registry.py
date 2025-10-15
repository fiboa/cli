import re

from vecorel_cli.registry import Registry, VecorelRegistry

from fiboa_cli.fiboa.version import spec_pattern

FIBOA_SPECIFICATION = "https://fiboa.org/specification/v0.3.0/schema.yaml"


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
        super().register_commands()

        from .create_stac import CreateFiboaStacCollection
        from .describe import DescribeFiboaFile
        from .improve import Improve
        from .rename_extension import RenameFiboaExtension

        self.set_command(CreateFiboaStacCollection)
        self.set_command(DescribeFiboaFile)
        self.set_command(RenameFiboaExtension)
        self.set_command(Improve)


Registry.instance = FiboaRegistry()
