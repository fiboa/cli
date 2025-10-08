import json
import os
import re
import sys
from datetime import date
from functools import cache

import requests
from vecorel_cli.basecommand import BaseCommand, runnable
from vecorel_cli.cli.options import VECOREL_TARGET
from vecorel_cli.convert import ConvertData
from vecorel_cli.create_stac import CreateStacCollection
from vecorel_cli.validate import ValidateData

from .registry import Registry

STAC_EXTENSION = "https://stac-extensions.github.io/web-map-links/v1.2.0/schema.json"


class Publish(BaseCommand):
    cmd_name = "publish"
    cmd_help = f"Convert and publish a {Registry.project} dataset to source coop."
    source_coop = "https://data.source.coop/fiboa/data"

    @staticmethod
    def get_cli_args():
        return {
            **ConvertData.get_cli_args(),
            "target": VECOREL_TARGET(folder=True),
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
        # override data survey location with env variable, e.g. for unmerged pull-requests
        data_survey = (
            os.getenv("FIBOA_DATA_SURVEY")
            or f"https://raw.githubusercontent.com/fiboa/data-survey/refs/heads/main/data/{base}.md"
        )
        response = requests.get(data_survey)
        assert response.ok, (
            f"Missing data survey {base}.md at {data_survey}. Can not auto-generate file"
        )
        return dict(re.findall(r"- \*\*(.+?):\*\* (.+?)\n", response.text))

    def readme_attribute_table(self, stac_data):
        cols = [["Property", "**Data Type**", "Description"]] + [
            [s["name"], re.search(r"\w+", s["type"])[0], ""]
            for s in stac_data["assets"]["data"]["table:columns"]
            if s["name"] != "geometry"
        ]
        widths = [max(len(c[i]) for c in cols) for i in range(3)]
        aligned_cols = [[f" {c:<{w}} " for c, w in zip(row, widths)] for row in cols]
        aligned_cols.insert(1, ["-" * (w + 2) for w in widths])
        return "\n".join(["|" + "|".join(cols) + "|" for cols in aligned_cols])

    def make_license(self):
        props = self.get_data_survey()
        text = ""
        if "license" in props:
            text += props["license"] + "\n\n"
        converter = self.converter
        if hasattr(converter, "LICENSE"):
            text += (
                converter.LICENSE["title"]
                if isinstance(converter.LICENSE, dict)
                else converter.LICENSE
            )
        return text

    def make_readme(self, file_name, stac):
        version = "0.3.0"  # TODO HOW TO GET VERSION?
        converter = self.converter
        stac_data = json.load(open(stac))
        count = stac_data["assets"]["data"]["table:row_count"]
        columns = self.readme_attribute_table(stac_data)
        props = self.get_data_survey()
        _download_urls = converter.get_urls().keys() or ["manually downloaded file"]
        downloaded_urls = "\n".join([("  - " + url) for url in _download_urls])

        return f"""# Field boundaries for {converter.short_name}

Provides {count} official field boundaries from {converter.short_name}.
It has been converted to a fiboa GeoParquet file from data obtained from {props["Data Provider (Legal Entity)"]}.

- **Source Data Provider:** [{props["Data Provider (Legal Entity)"]}]({props["Homepage"]})
- **Converted by:** {props["Submitter (Affiliation)"]}
- **License:** {props["License"]}
- **Projection:** {props["Projection"]}

---

- [Download the data as fiboa GeoParquet]({self.source_coop_data}{file_name}.parquet)
- [STAC Browser](https://radiantearth.github.io/stac-browser/#/external/data.source.coop/fiboa/data/{self.dataset}/stac/collection.json)
- [STAC Collection]({self.source_coop_data}stac/collection.json)
- [PMTiles]({self.source_coop_data}{file_name}.pmtiles)

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
        **kwargs,
    ):
        """
        Implement https://github.com/fiboa/data/blob/main/HOWTO.md#each-time-you-update-the-dataset

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
            os.environ.get("AWS_SECRET_ACCESS_KEY")
            and os.environ.get("AWS_ENDPOINT_URL") == "https://data.source.coop"
        )
        os.environ["AWS_ENDPOINT_URL"] = "https://data.source.coop"
        os.environ["AWS_REQUEST_CHECKSUM_CALCULATION"] = "WHEN_REQUIRED"

        collection_file = os.path.join(target, "collection.json")
        stac_directory = os.path.join(target, "stac")
        done_convert = os.path.exists(parquet_file) and os.path.exists(
            os.path.join(stac_directory, "collection.json")
        )

        if not done_convert:
            # fiboa convert xx_yy -o data/xx-yy.parquet -h https://data.source.coop/fiboa/xx-yy/ --collection
            self.success(f"Converting file for {self.dataset} to {parquet_file}")
            # ConvertData(self.dataset).run(parquet_file, **kwargs)
            try:
                CreateStacCollection().create_cli(parquet_file, collection_file)
            except Exception:
                import traceback

                traceback.print_exc()
            self.success("Done")
        else:
            self.success(f"Using existing file {parquet_file} for {self.dataset}")

        # fiboa validate data/xx-yy.parquet --data
        self.info(f"Validating {parquet_file}")
        ValidateData().validate(parquet_file, num=-1)
        self.log("\n  => VALID\n", "success")

        # mkdir data/stac; mv data/collection.json data/stac
        stac_target = os.path.join(stac_directory, "collection.json")
        if not done_convert:
            os.makedirs(stac_directory, exist_ok=True)
            data = json.load(open(collection_file))
            assert data["id"] == self.dataset, (
                f"Wrong collection dataset id: {data['id']} != {self.dataset}"
            )

            if STAC_EXTENSION not in data["stac_extensions"]:
                data["stac_extensions"].append(STAC_EXTENSION)
                data["links"].append(
                    {
                        "href": f"{self.source_coop_data}{file_name}.pmtiles",
                        "type": "application/vnd.pmtiles",
                        "rel": "pmtiles",
                    }
                )

            with open(stac_target, "w", encoding="utf-8") as f:
                json.dump(data, f)
            os.remove(collection_file)

        for required in ("README.md", "LICENSE.txt"):
            path = os.path.join(target, required)
            if not os.path.exists(path):
                self.warning(f"Missing {required}. Generating at {path}")
                if required == "README.md":
                    text = self.make_readme(
                        file_name=file_name,
                        stac=stac_target,
                    )
                else:
                    text = self.make_license()
                with open(path, "w") as f:
                    f.write(text)
                self.warning(f"Please complete the {path} before continuing")
                sys.exit(1)

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
            self.info(f"Get your credentials at {self.source_coop_data}manage/")
            self.info("  Then press 'ACCESS DATA',\n  and click 'Create API Key',")
            self.info(
                "  Run export AWS_ENDPOINT_URL=https://data.source.coop AWS_ACCESS_KEY_ID=<> AWS_SECRET_ACCESS_KEY=<>\n"
                "  where you copy-past the access key and secret",
            )
            self.error("Please set AWS_ env vars from source_coop")
            sys.exit(1)

        self.check_command("aws")
        self.exc(f"aws s3 sync {target} s3://fiboa/data/{self.dataset}/")
