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

    EXTENSIONS = getattr(base, "EXTENSIONS", None) or []
    EXTENSIONS = list(EXTENSIONS) + [
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


class EuroCropsConverterMixin:
    ec_mapping_csv = None
    mapping_file = None

    def __init__(self, *args, year=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Some meta-magic to reuse existing add_eurocrops routine
        attributes = "ID, SHORT_NAME, TITLE, DESCRIPTION, PROVIDERS, EXTENSIONS, COLUMNS, LICENSE".split(", ")
        base = {k: getattr(self, k.lower()) for k in attributes}
        for k, v in zip(attributes, add_eurocrops(base, year=year)):
            setattr(self, k.lower(), v)

    def convert(self, *args, **kwargs):
        self.mapping_file = kwargs.get("mapping_file")
        if not self.mapping_file:
            assert self.ec_mapping_csv is not None, "Specify ec_mapping_csv in Converter, e.g. find them at https://github.com/maja601/EuroCrops/tree/main/csvs/country_mappings"
        return super().convert(*args, **kwargs)

    def get_code_column(self, gdf):
        attribute = next(k for k, v in self.columns.items() if v == 'crop:code')
        col = gdf[attribute]
        # Should be corrected in original parser
        return col if col.dtype == 'object' else col.astype(str)

    def add_hcat(self, gdf):
        ec_mapping = load_ec_mapping(self.ec_mapping_csv, url=self.mapping_file)
        crop_code_col = self.get_code_column(gdf)

        def map_to(attribute):
            return {e["original_code"]: e[attribute] for e in ec_mapping}

        gdf['EC_trans_n'] = crop_code_col.map(map_to("translated_name"))
        gdf['EC_hcat_n'] = crop_code_col.map(map_to("HCAT3_name"))
        gdf['EC_hcat_c'] = crop_code_col.map(map_to("HCAT3_code"))
        return gdf

    def migrate(self, gdf):
        gdf = super().migrate(gdf)
        return self.add_hcat(gdf)


def ec_url(csv_file):
    return f"https://raw.githubusercontent.com/maja601/EuroCrops/refs/heads/main/csvs/country_mappings/{csv_file}"


def load_ec_mapping(csv_file=None, url=None):
    if not (csv_file or url):
        raise ValueError("Either csv_file or url must be specified")
    if not url:
        url = ec_url(csv_file)
    content = load_file(url)
    return list(csv.DictReader(StringIO(content.decode('utf-8'))))
