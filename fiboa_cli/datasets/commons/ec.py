import csv
from io import StringIO
from fiboa_cli.util import load_file


def add_eurocrops(base, year = None):
    if isinstance(base, dict):
        base = DictObject(base)

    ID = base.ID
    if not base.ID.startswith("ec_"):
        ID = "ec_" + ID

    SUFFIX = " - Eurocrops"
    if year is not None:
        SUFFIX += " " + str(year)

    TITLE = base.TITLE + SUFFIX

    SHORT_NAME = base.SHORT_NAME + SUFFIX

    DESCRIPTION = base.DESCRIPTION.strip() + """

This dataset is an extended version of the original dataset, with additional columns and attributes added by the EuroCrops project.

The project developed a new **Hierarchical Crop and Agriculture Taxonomy (HCAT)** that harmonises all declared crops across the European Union.
In the data you'll find this as additional attributes:

- `EC_trans_n`: The original crop name translated into English
- `EC_hcat_n`: The machine-readable HCAT name of the crop
- `EC_hcat_c`: The 10-digit HCAT code indicating the hierarchy of the crop
    """

    PROVIDERS = base.PROVIDERS + [
        {
            "name": "EuroCrops",
            "url": "https://github.com/maja601/EuroCrops",
            "roles": ["processor"]
        }
    ]

    EXTENSIONS = base.EXTENSIONS if hasattr(base, 'EXTENSIONS') else []
    EXTENSIONS = EXTENSIONS + [
        "https://fiboa.github.io/hcat-extension/v0.1.0/schema.yaml"
    ]

    COLUMNS = base.COLUMNS | {
        'EC_trans_n': 'ec:translated_name',
        'EC_hcat_n': 'ec:hcat_name',
        'EC_hcat_c': 'ec:hcat_code'
    }

    LICENSE = "CC-BY-SA-4.0"

    return ID, SHORT_NAME, TITLE, DESCRIPTION, PROVIDERS, EXTENSIONS, COLUMNS, LICENSE


class DictObject(object):
    def __init__(self, dict_):
        self.__dict__.update(dict_)


def load_ec_mapping(csv_file=None, url=None):
    if not (csv_file or url):
        raise ValueError("Either csv_file or url must be specified")
    if not url:
        url = f"https://raw.githubusercontent.com/maja601/EuroCrops/refs/heads/main/csvs/country_mappings/{csv_file}"
    content = load_file(url)
    return list(csv.DictReader(StringIO(content.decode('utf-8'))))
