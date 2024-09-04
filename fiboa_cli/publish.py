import os
import sys
import json
import requests

from .util import log
from fiboa_cli import list_all_converter_ids
from fiboa_cli.convert import convert
from fiboa_cli.validate import validate

STAC_EXTENSION = "https://stac-extensions.github.io/web-map-links/v1.2.0/schema.json"


def exc(cmd):
    assert os.system(cmd) == 0


def check_command(cmd, name=None):
    if os.system(f"{cmd} --version") != 0:
        log(f"Missing command {cmd}. Please install {name or cmd}", "error")
        sys.exit(1)


def publish(dataset, directory, cache, source_coop_extension):
    """
    Implement https://github.com/fiboa/data/blob/main/HOWTO.md#each-time-you-update-the-dataset

    You need GDAL 3.8 or later (for ogr2ogr), tippecanoe, and AWS CLI
    - https://gdal.org/
    - https://github.com/felt/tippecanoe
    - https://aws.amazon.com/cli/
    """
    assert dataset in list_all_converter_ids()
    os.makedirs(directory, exist_ok=True)

    for key in ("README.md", "LICENSE.txt"):
        path = os.path.join(directory, key)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Please create {path}")

    parent = os.path.dirname(directory)
    os.chdir(parent)

    if not source_coop_extension:
        source_coop_extension = dataset.replace("_", "-")

    file_name = source_coop_extension.replace("-", "_")  # not sure if we want this

    parquet_file = os.path.join(directory, f"{file_name}.parquet")
    source_coop_url = f"https://beta.source.coop/fiboa/{source_coop_extension}/"

    assert requests.get(f"https://api.source.coop/repositories/fiboa/{source_coop_extension}").status_code == 200, \
        f"Missing repo at {source_coop_url}"

    collection_file = os.path.join(directory, "collection.json")

    stac_directory = os.path.join(directory, "stac")
    done_convert = os.path.exists(parquet_file) and os.path.exists(os.path.join(stac_directory, "collection.json"))

    if not done_convert:
        # fiboa convert xx_yy -o data/xx-yy.parquet -h https://beta.source.coop/fiboa/xx-yy/ --collection
        log(f"Converting file for {dataset} to {parquet_file}\n", "success")
        convert(dataset, parquet_file, cache=cache, source_coop_url=source_coop_url, collection=True)
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
                "href": f"{source_coop_url}/{file_name}.pmtiles",
                "type": "application/vnd.pmtiles",
                "rel": "pmtiles"
            })

        with open(stac_target, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.remove(collection_file)

    pm_file = os.path.join(directory, f"{file_name}.pmtiles")
    if not os.path.exists(pm_file):
        log(f"ogr2ogr geo.json", "info")
        check_command("ogr2ogr", name="GDAL")
        exc(f"ogr2ogr -t_srs EPSG:4326 geo.json {parquet_file}")

        log(f"Running tippecanoe", "info")
        check_command("tippecanoe")
        exc(f"tippecanoe -zg --projection=EPSG:4326 -o {pm_file} -l {dataset} geo.json --drop-densest-as-needed")

        os.remove("geo.json")

    log(f"Uploading to aws", "info")
    if not os.environ.get("AWS_SESSION_TOKEN"):
        log(f"Get your credentials at {source_coop_url}download/", "info")
        log("  Then press 'ACCESS DATA',\n  and click 'GENERATE CREDENTIALS',", "info")
        log("  Under 'Usage example' there's a code block with EXPORT commands,\n"
            "  copy-paste this block in this terminal and re-run this command)", "info")

        log("Please set AWS_ env vars from source_coop", "error")
        sys.exit(1)
    check_command("aws")
    exc(f"aws s3 sync {directory} s3://us-west-2.opendata.source.coop/fiboa/{source_coop_extension}/")
