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
        "determination_datetime",
        "determination_method",
        "determination_details",
    ]

    def register_commands(self):
        super().register_commands()

        from .describe import DescribeFiboaFile

        self.set_command(DescribeFiboaFile)


Registry.instance = FiboaRegistry()
