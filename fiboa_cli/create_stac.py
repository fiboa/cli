import click
from geopandas import GeoDataFrame
from vecorel_cli.cli.options import JSON_INDENT, VECOREL_FILE_ARG, VECOREL_TARGET_CONSOLE
from vecorel_cli.create_stac import CreateStacCollection as Base
from vecorel_cli.registry import VecorelRegistry
from vecorel_cli.vecorel.collection import Collection

from fiboa_cli.fiboa.version import get_versions

# The fiboa properties mean the same in every dataset; a converter's own columns are described per dataset
DESCRIPTIONS = {
    "id": "Unique identifier",
    "collection": "The collection identifier",
    "inspire:id": "The INSPIRE identifier",
    "determination:datetime": "Timestamp of the determination of the field boundary",
    "metrics:area": "Field area in square meters",
    "metrics:perimeter": "Field perimeter in meters",
    "crop:code_list": "A link to the code list",
    "crop:code": "The crop code",
    "crop:name": "Crop name in the original language",
    "crop:name_en": "Crop name in English",
    "hcat:name": "The machine-readable HCAT name of the crop",
    "hcat:code": "The 10-digit HCAT code indicating the hierarchy of the crop",
    "hcat:name_en": "The HCAT crop name translated into English",
    "admin:country_code": "ISO 3166-1 alpha-2 country code",
    "admin:subdivision_code": "ISO 3166-2 principal subdivision code (e.g. province or state)",
}


class CreateStacCollection(Base):
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
                default=CreateStacCollection.temporal_property,
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

    def create_from_file(self, *args, **kwargs) -> dict:
        stac = super().create_from_file(*args, **kwargs)
        for column in stac["assets"]["data"].get("table:columns", []):
            if column["name"] in DESCRIPTIONS:
                column.setdefault("description", DESCRIPTIONS[column["name"]])
        return stac
