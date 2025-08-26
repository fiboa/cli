from vecorel_cli.registry import Registry, VecorelRegistry


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
    ignored_datasets = VecorelRegistry.ignored_datasets + ["es.py"]

    def register_commands(self):
        super().register_commands()

        from .describe import DescribeFiboaFile
        from .rename_extension import RenameFiboaExtension

        self.set_command(DescribeFiboaFile)
        self.set_command(RenameFiboaExtension)


Registry.instance = FiboaRegistry()
