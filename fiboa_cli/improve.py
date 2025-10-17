import json

import click
import spdx_license_list
from geopandas import GeoDataFrame
from vecorel_cli.basecommand import runnable
from vecorel_cli.encoding.auto import create_encoding
from vecorel_cli.improve import ImproveData
from vecorel_cli.vecorel.collection import Collection
from vecorel_cli.vecorel.extensions import ADMIN_DIVISION
from vecorel_cli.vecorel.version import sdl_uri

from fiboa_cli.conversion.fiboa_converter import FiboaBaseConverter
from fiboa_cli.datasets.commons.ec import AddHCATMixin
from fiboa_cli.datasets.commons.hcat import CROP_EXTENSION, HCAT_EXTENSION
from fiboa_cli.registry import FIBOA_SPECIFICATION


class Improve(ImproveData):
    @staticmethod
    def get_cli_args():
        return {
            **ImproveData.get_cli_args(),
            "add-hcat": click.option(
                "--add-hcat",
                "-hcat",
                type=str,
                help="Adds hcat-extension and columns to the collection, based on the crop:code column and a mapping file. Requires a mapping file as argument, e.g. 'at_2021.csv', find them at https://github.com/maja601/EuroCrops/tree/main/csvs/country_mappings",
            ),
        }

    @runnable
    def improve_file(
        self, source, target=None, compression=None, geoparquet_version=None, indent=None, **kwargs
    ):
        # Override method to be able to convert input from fiboa-0.2.0 to fiboa-0.3.0
        if not target:
            target = source

        input_encoding = create_encoding(source)
        geodata = input_encoding.read()
        collection = input_encoding.get_collection()

        if not collection:
            # Try to migrate from fiboa-0.2.0 to fiboa-0.3.0
            metadata = input_encoding.get_metadata()
            if b"fiboa" in metadata:
                fiboa_2 = json.loads(metadata[b"fiboa"].decode("utf-8"))
                geodata, collection = self.migrate_fiboa_2(geodata, fiboa_2, source.name)

        geodata, collection = self.improve(geodata, collection=collection, **kwargs)

        output_encoding = create_encoding(target)
        output_encoding.set_collection(collection)
        output_encoding.write(
            geodata,
            compression=compression,
            geoparquet_version=geoparquet_version,
            indent=indent,
        )
        return target

    def improve(
        self, gdf: GeoDataFrame, collection: Collection, add_hcat: str = None, **kwargs
    ) -> tuple[GeoDataFrame, Collection]:
        gdf, collection = super().improve(gdf, collection, **kwargs)
        # Add HCAT
        if add_hcat:
            gdf, collection = self.add_hcat(gdf, collection, add_hcat)
            self.info("Added HCAT columns and extension")
        return gdf, collection

    def add_hcat(self, gdf, collection, mapping_file):
        if "crop:code" not in gdf.columns:
            raise Exception("Missing crop:code column in dataset")

        is_url = "/" in mapping_file
        _mapping_file = mapping_file

        # Simplest way to reuse functionality from AddHCATMixin
        class HCAT(AddHCATMixin, FiboaBaseConverter):
            columns = {"crop:code": "crop:code"}
            ec_mapping_csv = None if is_url else _mapping_file
            mapping_file = _mapping_file if is_url else None

        for schemas in collection["schemas"].values():
            if HCAT_EXTENSION not in schemas:
                schemas.append(HCAT_EXTENSION)

        return HCAT().add_hcat(gdf), collection

    def migrate_fiboa_2(
        self, geodata, original: Collection, file_name: str
    ) -> tuple[GeoDataFrame, Collection]:
        if original["fiboa_version"] != "0.2.0":
            self.warning(
                f"Not migrating from fiboa version {original['fiboa_version']}, can only migrate fiboa from 0.2.0"
            )
            return geodata, original

        self.info(f"Migrating data from fiboa version {original['fiboa_version']}")
        schemas = {"https://vecorel.org/specification/v0.1.0/schema.yaml", FIBOA_SPECIFICATION}
        for e in original.get("fiboa_extensions", []):
            if e in EXTENSION_MAPPING:
                schemas.add(EXTENSION_MAPPING[e])

        base = {k: original[k] for k in ("title", "description", "attribution") if k in original}
        collection_id = original.get("id") or file_name.split(".")[0]

        collection = Collection(
            {"schemas": {collection_id: list(schemas)}, "collection": collection_id} | base
        )

        # Migrate custom schemas
        if "fiboa_custom_schemas" in original:
            collection["schemas:custom"] = {
                "$schema": "https://vecorel.org/sdl/v0.2.0/schema.json",
                "required": [],
                "collection": {},
            } | original["fiboa_custom_schemas"]

        # Take first provider json, make string out of it
        if "providers" in original:
            provider = next(iter(original["providers"]))
            collection["provider"] = f"{provider['name']} <{provider['url']}>"

        # Transform license links to string
        if original.get("license"):
            if original["license"] in spdx_license_list.LICENSES or "<" in original["license"]:
                collection["license"] = original["license"]
        if "license" not in collection:
            _licenses = [link for link in original.get("links", []) if link.get("rel") == "license"]
            if _licenses:
                collection["license"] = f"{_licenses[0]['title']} <{_licenses[0]['href']}>"

        # Rename columns
        rename = {
            k: v
            for k, v in (
                ("determination_datetime", "determination:datetime"),
                ("determination_method", "determination:method"),
                ("metrics_perimeter", "metrics:perimeter"),
            )
            if k in original
        }

        # Transform area from ha to m2
        if "area" in geodata.columns:
            geodata["area"] *= 10000
            rename["area"] = "metrics:area"

        geodata.rename(rename, axis=1, inplace=True)
        return geodata, collection


EXTENSION_MAPPING = {
    "https://fiboa.github.io/hcat-extension/v0.2.0/schema.yaml": HCAT_EXTENSION,
    "https://fiboa.github.io/crop-extension/v0.1.0/schema.yaml": CROP_EXTENSION,
    "https://fiboa.github.io/inspire-extension/v0.1.0/schema.yaml": "https://fiboa.org/inspire-extension/v0.3.0/schema.yaml",
    "https://fiboa.github.io/schema/v0.1.0/schema.json": sdl_uri,
    "https://fiboa.github.io/administrative-division-extension/v0.1.0/schema.yaml": ADMIN_DIVISION,
}
