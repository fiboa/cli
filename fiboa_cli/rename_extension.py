import os
import re

from .create_geoparquet import create_geoparquet
from .util import log


def replace_in_str(content, search, replace):
    if isinstance(search, list) and isinstance(replace, list) and len(search) != len(replace):
        raise ValueError("Search and replace lists must have the same length")

    if isinstance(search, str):
        return content.replace(search, replace)
    elif isinstance(search, re.Pattern):
        return content.replace(search, replace)
    elif isinstance(search, list) and isinstance(replace, list):
        for s, r in zip(search, replace):
            content = replace_in_str(content, s, r)
        return content
    elif isinstance(search, list):
        for s in search:
            content = replace_in_str(content, s, replace)
        return content
    else:
        raise ValueError(f"Invalid search type: {type(search)}")


def replace_in_file(file, search, replace):
    try:
        with open(file, "r+") as f:
            content = f.read()
            content = replace_in_str(content, search, replace)
            f.seek(0)
            f.write(content)
            f.truncate()
        log(f"Updated {file}", "success")
    except Exception as e:
        log(f"Can't update {file}: {e}", "error")


def rename_extension(folder, title, slug, gh_org="fiboa", prefix=None):
    if prefix is None:
        prefix = "template"

    README = os.path.join(folder, "README.md")
    CHANGELOG = os.path.join(folder, "CHANGELOG.md")
    PIPFILE = os.path.join(folder, "Pipfile")
    JSON_COLLECTION = os.path.join(folder, "examples/geojson/collection.json")
    GEOJSON_FEATURE = os.path.join(folder, "examples/geojson/example.json")
    GEOPARQUET = os.path.join(folder, "examples/geoparquet/example.parquet")
    SCHEMA = os.path.join(folder, "schema/schema.yaml")

    if prefix == "":
        PREFIX_CODE = ""
        PREFIX_TITLE = "none"
    else:
        PREFIX_CODE = f"{prefix}:"
        PREFIX_TITLE = prefix

    GH_SEARCH = ["/extension-template/", "fiboa.github.io"]
    GH_REPLACE = [f"/{slug}/", f"{gh_org}.github.io"]
    replace_in_file(PIPFILE, GH_SEARCH, GH_REPLACE)
    replace_in_file(JSON_COLLECTION, GH_SEARCH, GH_REPLACE)

    replace_in_file(CHANGELOG, "/fiboa/extension-template/", f"/{gh_org}/{slug}/")

    PREFIX_SEARCH = "template:"
    replace_in_file(GEOJSON_FEATURE, PREFIX_SEARCH, PREFIX_CODE)
    replace_in_file(SCHEMA, PREFIX_SEARCH, PREFIX_CODE)

    README_SEARCH = GH_SEARCH + [
        "Template Extension",
        "- **Title:** Template",
        "- **Property Name Prefix:** template",
        "| template:",
    ]
    README_REPLACE = GH_REPLACE + [
        f"{title} Extension",
        f"- **Title:** {title}",
        f"- **Property Name Prefix:** {PREFIX_TITLE}",
        f"| {PREFIX_CODE}",
    ]
    replace_in_file(README, README_SEARCH, README_REPLACE)

    try:
        config = {
            "files": [GEOJSON_FEATURE],
            "out": GEOPARQUET,
            "schema": None,
            "collection": JSON_COLLECTION,
            "extension_schemas": {f"https://{gh_org}.github.io/{slug}/v0.1.0/schema.yaml": SCHEMA},
        }
        create_geoparquet(config)
    except Exception as e:
        log(f"Can't update {GEOPARQUET}: {e}", "error")
