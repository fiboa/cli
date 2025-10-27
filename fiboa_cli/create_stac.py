import click
from geopandas import GeoDataFrame
from vecorel_cli.cli.options import JSON_INDENT, VECOREL_FILE_ARG, VECOREL_TARGET_CONSOLE
from vecorel_cli.create_stac import CreateStacCollection
from vecorel_cli.registry import VecorelRegistry
from vecorel_cli.vecorel.collection import Collection

from fiboa_cli.fiboa.version import get_versions


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

    def create(self, collection: Collection, gdf: GeoDataFrame, *args, **kwargs) -> dict:
        data = super().create(collection, gdf, *args, **kwargs)
        vecorel = VecorelRegistry()
        data["assets"]["data"]["processing:software"].setdefault(
            vecorel.name, vecorel.get_version()
        )
        schemas = collection.get_schemas()
        vecorel_version, _, fiboa_version, _, extensions = get_versions(
            next(iter(schemas.values()))
        )
        data["fiboa_version"] = fiboa_version
        data.setdefault("vecorel_version", vecorel_version)
        data.setdefault("vecorel_extensions", {k: list(v) for k, v in schemas.items()})

        return data
