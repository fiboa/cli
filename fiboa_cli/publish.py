from datetime import date
import os
import sys
import json
from functools import cache

import requests
import re

from .util import log
from fiboa_cli import list_all_converter_ids, version
from fiboa_cli.convert import convert, read_converter
from fiboa_cli.validate import validate

STAC_EXTENSION = "https://stac-extensions.github.io/web-map-links/v1.2.0/schema.json"


def exc(cmd):
    assert os.system(cmd) == 0


def check_command(cmd, name=None):
    if os.system(f"{cmd} --version") != 0:
        log(f"Missing command {cmd}. Please install {name or cmd}", "error")
        sys.exit(1)


@cache
def get_data_survey(dataset):
    base = dataset.replace("_", "-").upper()
    # override data survey location with env variable, e.g. for unmerged pull-requests
    data_survey = os.getenv("FIBOA_DATA_SURVEY") or \
        f"https://raw.githubusercontent.com/fiboa/data-survey/refs/heads/main/data/{base}.md"
    response = requests.get(data_survey)
    assert response.ok, f"Missing data survey {base}.md at {data_survey}. Can not auto-generate file"
    return dict(re.findall(r"- \*\*(.+?):\*\* (.+?)\n", response.text))


def readme_attribute_table(stac_data):
    cols = (
        [["Property", "**Data Type**", "Description"]] +
        [[s['name'], re.search(r"\w+", s["type"])[0], ""] for s in stac_data["assets"]["data"]["table:columns"] if s['name'] != 'geometry']
    )
    widths = [max(len(c[i]) for c in cols) for i in range(3)]
    aligned_cols = [[f" {c:<{w}} " for c, w in zip(row, widths)] for row in cols]
    aligned_cols.insert(1, ["-" * (w+2) for w in widths])
    return "\n".join(["|" + "|".join(cols) + "|" for cols in aligned_cols])


def make_license(dataset, **kwargs):
    props = get_data_survey(dataset)
    text = ""
    if "license" in props:
        text += props["license"] + "\n\n"
    converter = read_converter(dataset)
    if hasattr(converter, "LICENSE"):
        text += converter.LICENSE["title"] if isinstance(converter.LICENSE, dict) else converter.LICENSE
    return text


def make_readme(dataset, file_name, stac, source_coop_extension):
    source_coop_data = f"https://data.source.coop/fiboa/{source_coop_extension}/"

    converter = read_converter(dataset)
    stac_data = json.load(open(stac))
    count = stac_data["assets"]["data"]["table:row_count"]
    columns = readme_attribute_table(stac_data)
    props = get_data_survey(dataset)
    if isinstance(converter.SOURCES, str):
        download_url = converter.SOURCES
    elif isinstance(converter.SOURCES, dict):
        download_url = next(iter(converter.SOURCES))
    else:
        download_url = "manually downloaded file"

    return f"""# Field boundaries for {converter.SHORT_NAME}

Provides {count} official field boundaries from {converter.SHORT_NAME}.
It has been converted to a fiboa GeoParquet file from data obtained from {props['Data Provider (Legal Entity)']}.

- **Source Data Provider:** [{props['Data Provider (Legal Entity)']}]({props['Homepage']})
- **Converted by:** {props['Submitter (Affiliation)']}
- **License:** {props['License']}
- **Projection:** {props['Projection']}

---

- [Download the data as fiboa GeoParquet]({source_coop_data}{file_name}.parquet)
- [STAC Browser](https://radiantearth.github.io/stac-browser/#/external/data.source.coop/{source_coop_extension}/stac/collection.json)
- [STAC Collection]({source_coop_data}{source_coop_extension}/stac/collection.json)
- [PMTiles]({source_coop_data}{source_coop_extension}/{file_name}.pmtiles)

## Columns

{columns}

## Lineage

- Data downloaded on {date.today()} from {download_url} .
- Converted to GeoParquet using [fiboa-cli](https://github.com/fiboa/cli), version {version.__version__}
"""


def publish(dataset, directory, cache, source_coop_extension, input_files=None):
    """
    Implement https://github.com/fiboa/data/blob/main/HOWTO.md#each-time-you-update-the-dataset

    You need GDAL 3.8 or later (for ogr2ogr) with libgdal-arrow-parquet, tippecanoe, and AWS CLI
    - https://gdal.org/
    - https://github.com/felt/tippecanoe
    - https://aws.amazon.com/cli/
    """
    assert dataset in list_all_converter_ids()
    os.makedirs(directory, exist_ok=True)

    parent = os.path.dirname(directory)
    os.chdir(parent)

    if not source_coop_extension:
        source_coop_extension = dataset.replace("_", "-")

    file_name = source_coop_extension.replace("-", "_")  # not sure if we want this

    parquet_file = os.path.join(directory, f"{file_name}.parquet")
    source_coop_url = f"https://source.coop/fiboa/{source_coop_extension}/"
    source_coop_data = f"https://data.source.coop/fiboa/{source_coop_extension}/"

    assert requests.get(f"https://source.coop/api/v1/repositories/fiboa/{source_coop_extension}").status_code == 200, \
        f"Missing repo at {source_coop_url}"

    collection_file = os.path.join(directory, "collection.json")

    stac_directory = os.path.join(directory, "stac")
    done_convert = os.path.exists(parquet_file) and os.path.exists(os.path.join(stac_directory, "collection.json"))

    if not done_convert:
        # fiboa convert xx_yy -o data/xx-yy.parquet -h https://data.source.coop/fiboa/xx-yy/ --collection
        log(f"Converting file for {dataset} to {parquet_file}\n", "success")
        convert(dataset, parquet_file, cache=cache, source_coop_url=source_coop_url, collection=True, input_files=input_files)
        log(f"Done\n", "success")
    else:
        log(f"Using existing file {parquet_file} for {dataset}\n", "success")

    # fiboa validate data/xx-yy.parquet --data
    log(f"Validating {parquet_file}", "info")
    result = validate(parquet_file, config={"data": True})
    if result:
        log("\n  => VALID\n", "success")
    else:
        log("\n  => INVALID\n", "error")
        sys.exit(1)

    # mkdir data/stac; mv data/collection.json data/stac
    stac_target = os.path.join(stac_directory, "collection.json")
    if not done_convert:
        os.makedirs(stac_directory, exist_ok=True)
        data = json.load(open(collection_file))
        assert data["id"] == dataset, f"Wrong collection dataset id: {data['id']} != {dataset}"

        if STAC_EXTENSION not in data["stac_extensions"]:
            data["stac_extensions"].append(STAC_EXTENSION)
            data["links"].append({
                "href": f"{source_coop_data}{file_name}.pmtiles",
                "type": "application/vnd.pmtiles",
                "rel": "pmtiles"
            })

        with open(stac_target, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.remove(collection_file)

    for required in ("README.md", "LICENSE.txt"):
        path = os.path.join(directory, required)
        if not os.path.exists(path):
            log(f"Missing {required}. Generating at {path}", "warning")
            if required == "README.md":
                text = make_readme(dataset, file_name=file_name, stac=stac_target, source_coop_extension=source_coop_extension)
            else:
                text = make_license(dataset, source_coop_url=source_coop_url, file_name=file_name, stac=stac_target)
            with open(path, "w") as f:
                f.write(text)
            log(f"Please complete the {path} before continuing", "warning")
            sys.exit(1)

    pm_file = os.path.join(directory, f"{file_name}.pmtiles")
    if not os.path.exists(pm_file):
        log(f"Running ogr2ogr | tippecanoe", "info")
        check_command("tippecanoe")
        check_command("ogr2ogr", name="GDAL")
        exc(f"ogr2ogr -t_srs EPSG:4326 -f geojson /vsistdout/ {parquet_file} | tippecanoe -zg --projection=EPSG:4326 -o {pm_file} -l {dataset} --drop-densest-as-needed")

    log(f"Uploading to aws", "info")
    if not os.environ.get("AWS_SECRET_ACCESS_KEY"):
        log(f"Get your credentials at {source_coop_url}manage/", "info")
        log("  Then press 'ACCESS DATA',\n  and click 'Create API Key',", "info")
        log("  Run export AWS_ENDPOINT_URL=https://data.source.coop AWS_ACCESS_KEY_ID=<> AWS_SECRET_ACCESS_KEY=<>\n"
            "  where you copy-past the access key and secret", "info")
        log("Please set AWS_ env vars from source_coop", "error")
        sys.exit(1)

    assert os.environ.get("AWS_ENDPOINT_URL") == "https://data.source.coop", "Missing AWS_ENDPOINT_URL env var"
    check_command("aws")
    exc(f"aws s3 sync {directory} s3://fiboa/{source_coop_extension}/")
