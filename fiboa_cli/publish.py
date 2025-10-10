import json
import os
import re
import sys
from datetime import date
from functools import cache
from pathlib import Path

import click
import requests
from vecorel_cli.basecommand import BaseCommand, runnable
from vecorel_cli.cli.options import VECOREL_TARGET
from vecorel_cli.convert import ConvertData
from vecorel_cli.create_stac import CreateStacCollection
from vecorel_cli.validate import ValidateData

from .registry import Registry

STAC_EXTENSION = "https://stac-extensions.github.io/web-map-links/v1.2.0/schema.json"
DESCRIPTIONS = {
    "id": "Unique identifier",
    "collection": "The collection identifier",
    "inspire:id": "The INSPIRE identifier",
    "determination:datetime": "Timestamp of the determination of the field boundary",
    "metrics:area": "Field area in square meters",
    "metrics:perimeter": "Field perimeter in square meters",
    "crop:code_list": "A link to the code list",
    "crop:code": "The crop code",
    "crop:name": "Crop name in the original language",
    "crop:name_en": "Crop name in English",
    "hcat:name": "The machine-readable HCAT name of the crop",
    "hcat:code": "The 10-digit HCAT code indicating the hierarchy of the crop",
    "hcat:name_en": "The HCAT crop name translated into English",
}


class Publish(BaseCommand):
    cmd_name = "publish"
    cmd_help = f"Convert and publish a {Registry.project} dataset to source coop."
    source_coop = "https://data.source.coop/fiboa/data"

    @staticmethod
    def get_cli_args():
        return {
            **ConvertData.get_cli_args(),
            "target": VECOREL_TARGET(folder=True),
            "generate_meta": click.option(
                "--generate-meta",
                "-gm",
                is_flag=True,
                type=click.BOOL,
                help="Generate README.txt and LICENSE.txt for the dataset if not present.",
                default=False,
            ),
        }

    @staticmethod
    def get_cli_callback(cmd):
        def callback(dataset, *args, **kwargs):
            return Publish(dataset).run(*args, **kwargs)

        return callback

    def __init__(self, dataset: str):
        super().__init__()
        self.cmd_title = f"Convert {dataset}"
        self.dataset = dataset
        self.source_coop_data = f"{self.source_coop}/{self.dataset}"

        if ConvertData.converters.is_converter(self.dataset):
            raise Exception(f"'{self.dataset}' is not a converter")
        try:
            self.converter = ConvertData.converters.load(self.dataset)
        except (ImportError, NameError, OSError, RuntimeError, SyntaxError) as e:
            raise Exception(f"Converter for '{self.dataset}' not available or faulty: {e}") from e

    def exc(self, cmd):
        assert os.system(cmd) == 0

    def check_command(self, cmd, name=None):
        if os.system(f"{cmd} --version") != 0:
            self.error(f"Missing command {cmd}. Please install {name or cmd}")
            sys.exit(1)

    @cache
    def get_data_survey(self):
        base = self.dataset.replace("_", "-").upper()
        mapping = {
            "Data Provider (Legal Entity)": "provider",
            "Submitter (Affiliation)": "submitter",
        }
        # override data survey location with env variable, e.g. for unmerged pull-requests
        data_survey = (
            os.getenv("FIBOA_DATA_SURVEY")
            or f"https://raw.githubusercontent.com/fiboa/data-survey/refs/heads/main/data/{base}.md"
        )
        response = requests.get(data_survey)
        data = {
            "provider": self.converter.provider,
            "license": self.converter.license,
            "projection": "",
            "homepage": "",
            "submitter": "Fiboa project",
        }
        properties = {}
        if not response.ok:
            self.warning(
                f"Missing data survey {base}.md at {data_survey}. Can not auto-generate file"
            )
        else:
            data.update(dict(re.findall(r"- \*\*(.+?):\*\* (.+?)\n", response.text)))
            properties = {
                mapping.get(a.lower(), a.lower()): b.strip()
                for a, b in re.findall(r"\n\|\s*(\w+)[^|]*\|[^|]*\|[^|]*\|([^|]*)\|", response.text)
            }

        return data, properties

    def readme_attribute_table(self, stac_data, properties):
        def description(name):
            m = self.converter.columns
            reverse = dict(zip(m.values(), m.keys()))
            return (
                properties.get(reverse.get(name))
                or properties.get(name)
                or DESCRIPTIONS.get(name, "")
            )

        cols = [["Property", "**Data Type**", "Description"]] + [
            [
                s["name"],
                re.search(r"\w+", s["type"])[0],
                description(s["name"]),
            ]
            for s in stac_data["assets"]["data"]["table:columns"]
            if s["name"] not in ("geometry", "bbox", "collection")
        ]
        widths = [max(len(c[i]) for c in cols) for i in range(3)]
        aligned_cols = [[f" {c:<{w}} " for c, w in zip(row, widths)] for row in cols]
        aligned_cols.insert(1, ["-" * (w + 2) for w in widths])
        return "\n".join(["|" + "|".join(cols) + "|" for cols in aligned_cols])

    def make_license(self):
        text = ""
        try:
            data, properties = self.get_data_survey()
            text = data["license"]
            if getattr(self.converter, "license") not in (None, "", data["license"]):
                text += "\n" + self.converter.license + "\n"

            if "<(https://" not in text:
                # Include full-license text
                import spdx_license_list

                if text in spdx_license_list.LICENSES:
                    response = requests.get(
                        f"https://raw.githubusercontent.com/spdx/license-list-data/refs/heads/main/text/{text}.txt"
                    )
                    if response.ok:
                        text += f"\n\n{response.text}\n"
                else:
                    self.warning(f"License {text} could not be found in SPDX license list")

        except Exception as e:
            self.exception(e)
        return text

    def make_readme(self, file_name, stac):
        version = "0.3.0"  # TODO HOW TO GET VERSION?
        converter = self.converter
        stac_data = json.load(open(stac))
        count = stac_data["assets"]["data"]["table:row_count"]
        data, properties = self.get_data_survey()
        columns = self.readme_attribute_table(stac_data, properties)
        urls = converter.get_urls() or "manually downloaded file"
        urls = urls.keys() if isinstance(urls, dict) else [urls]
        downloaded_urls = "\n".join([("  - " + url) for url in urls])

        return f"""# Field boundaries for {converter.short_name}

Provides {count} official field boundaries from {converter.short_name}.
It has been converted to a fiboa GeoParquet file from data obtained from {data["provider"]}.

- **Source Data Provider:** [{data["provider"]}]({data["homepage"]})
- **Converted by:** {data["submitter"]}
- **License:** {data["license"]}
- **Projection:** {data["projection"]}

---

- [Download the data as fiboa GeoParquet]({self.source_coop_data}/{file_name}.parquet)
- [STAC Browser](https://radiantearth.github.io/stac-browser/#/external/data.source.coop/fiboa/data/{self.dataset}/stac/collection.json)
- [STAC Collection]({self.source_coop_data}/stac/collection.json)
- [PMTiles]({self.source_coop_data}/{file_name}.pmtiles)

## Columns

{columns}

## Lineage

- Data downloaded on {date.today()} from:
{downloaded_urls}
- Converted to GeoParquet using [fiboa-cli](https://github.com/fiboa/cli), version {version}
"""

    @runnable
    def publish(
        self,
        target,
        generate_meta=False,
        **kwargs,
    ):
        """
        You need GDAL 3.8 or later (for ogr2ogr) with libgdal-arrow-parquet, tippecanoe, and AWS CLI
        - https://gdal.org/
        - https://github.com/felt/tippecanoe
        - https://aws.amazon.com/cli/
        """
        os.makedirs(target, exist_ok=True)

        file_name = self.dataset
        if not kwargs["variant"] and self.converter.variants:
            kwargs["variant"] = next(iter(self.converter.variants))
        if kwargs["variant"]:
            file_name += f"-{kwargs['variant']}"
        parquet_file = os.path.join(target, f"{file_name}.parquet")

        has_write_access = bool(
            os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY")
        )

        stac_file = os.path.join(target, "stac", "collection.json")

        ## Create parquet file
        if not os.path.exists(parquet_file):
            self.info(f"Converting file for {self.dataset} to {parquet_file}")
            ConvertData(self.dataset).run(parquet_file, **kwargs)
            self.success(f"Converted file for {self.dataset} to {parquet_file}")
        else:
            self.success(f"Using existing file {parquet_file} for {self.dataset}")

        ## Validate parquet file, we only want to publish valid files
        self.info(f"Validating {parquet_file}")
        ValidateData().validate(parquet_file, num=-1)
        self.log("\n  => VALID\n", "success")

        ## Create STAC collection.json
        self.create_stac_collection(target, file_name, parquet_file, stac_file)

        if generate_meta:
            self.generate_meta(target, file_name, stac_file)

        pm_file = os.path.join(target, f"{file_name}.pmtiles")
        if not os.path.exists(pm_file):
            self.info("Running ogr2ogr | tippecanoe")
            self.check_command("tippecanoe")
            self.check_command("ogr2ogr", name="GDAL")
            self.exc(
                f"ogr2ogr -t_srs EPSG:4326 -f geojson /vsistdout/ {parquet_file} | tippecanoe -zg --projection=EPSG:4326 -o {pm_file} -l {self.dataset} --drop-densest-as-needed"
            )

        self.info("Uploading to aws")
        if not has_write_access:
            self.info("Get your credentials through the source coop organization.")
            self.info("Login to AWS Console and generate an access key:")
            self.info(
                "  - In AWS console, click on account (right top) press 'Security credentials',"
            )
            self.info("  - Go to 'Access keys' and press 'Create access key'")
            self.info(
                "  - Run export WS_ACCESS_KEY_ID=<> AWS_SECRET_ACCESS_KEY=<>\n"
                "    where you copy-past the access key and secret",
            )
            self.error("Please set AWS_ env vars from source_coop")
            sys.exit(1)

        self.check_command("aws")
        self.exc(
            f"aws s3 sync {target} s3://us-west-2.opendata.source.coop/fiboa/data/{self.dataset}/"
        )

    def create_stac_collection(self, target, file_name, parquet_file, stac_file):
        p_stac = Path(stac_file)
        if p_stac.exists() and p_stac.stat().st_mtime >= Path(parquet_file).stat().st_mtime:
            return

        self.success(f"Creating STAC collection.json for {parquet_file}")
        p_stac.parent.mkdir(exist_ok=True)
        CreateStacCollection().create_cli(parquet_file, stac_file)

        os.makedirs(os.path.join(target, "stac"), exist_ok=True)
        data = json.load(open(stac_file, "r"))
        assert data["id"] == self.dataset, (
            f"Wrong collection dataset id: {data['id']} != {self.dataset}, for {stac_file}"
        )

        data["assets"]["data"]["href"] = f"{self.source_coop_data}/{file_name}.parquet"

        if STAC_EXTENSION not in data["stac_extensions"]:
            data["stac_extensions"].append(STAC_EXTENSION)

        if not any(d.get("rel") == "pmtiles" for d in data["links"]):
            data["links"].append(
                {
                    "href": f"{self.source_coop_data}/{file_name}.pmtiles",
                    "type": "application/vnd.pmtiles",
                    "rel": "pmtiles",
                }
            )

        with open(stac_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def generate_meta(self, target, file_name, stac_file):
        for required in ("README.md", "LICENSE.txt"):
            path = os.path.join(target, required)
            if not os.path.exists(path):
                self.warning(f"Missing {required}. Generating at {path}")
                if required == "README.md":
                    text = self.make_readme(
                        file_name=file_name,
                        stac=stac_file,
                    )
                else:
                    text = self.make_license()
                self.info(
                    f"\nGenerated the following file {required}:\n{'-' * 80}\n\n{text}\n{'-' * 80}\n"
                )
                action = input("Do you want to Continue (C), Edit (E) or Abort (A)?")
                if action.lower() not in "ce":
                    self.warning("Bailing out")
                    sys.exit(1)
                with open(path, "w") as f:
                    f.write(text)
                if action.lower() == "e":
                    with open(path, "w") as f:
                        f.write(text)
                    editor = os.getenv("EDITOR") or "nano"
                    os.system(f"{editor} {path}")
