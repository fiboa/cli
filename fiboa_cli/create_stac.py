import click
from vecorel_cli.cli.options import JSON_INDENT, VECOREL_FILE_ARG, VECOREL_TARGET_CONSOLE
from vecorel_cli.create_stac import CreateStacCollection


class CreateFiboaStacCollection(CreateStacCollection):
    temporal_property = "determination:datetime"

    @staticmethod
    def get_cli_args():
        return {
            "source": VECOREL_FILE_ARG,
            "target": VECOREL_TARGET_CONSOLE,
            "indent": JSON_INDENT,
            "temporal": click.option(
                "temporal_property",
                "--temporal",
                "-t",
                type=click.STRING,
                help="The temporal property to use for the temporal extent.",
                show_default=True,
                default=CreateFiboaStacCollection.temporal_property,
            ),
            # todo: allow additional parameters for missing data in the collection?
            # https://stackoverflow.com/questions/36513706/python-click-pass-unspecified-number-of-kwargs
        }
