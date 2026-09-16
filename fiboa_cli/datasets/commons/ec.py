import csv
from io import StringIO

from vecorel_cli.vecorel.util import load_file

from fiboa_cli.datasets.commons.hcat import AddHCATMixin


class EuroCropsConverterMixin(AddHCATMixin):
    """
    Adds HCAT columns to a GeoDataFrame, useful for transforming datasets supplied by the Eurocrops project.
    The Eurocrops files have their own column names, so we need to map them to HCAT extension names.
    Also modifies the dataset title and provider to reflect the source.
    """

    ec_year = None
    hcat_columns = {
        "EC_trans_n": "hcat:name_en",
        "EC_hcat_n": "hcat:name",
        "EC_hcat_c": "hcat:code",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.id.startswith("ec_"):
            self.id = "ec_" + self.id
        suffix = " - Eurocrops"
        if self.ec_year is not None:
            suffix = f"{suffix} {self.ec_year}"

        self.title += suffix
        self.short_name += suffix

        provider = "EuroCrops <https://github.com/maja601/EuroCrops>"
        self.provider = (f"{self.provider}, {provider}") if self.provider else provider
        self.license = "CC-BY-SA-4.0"


def ec_url(csv_file):
    return f"https://raw.githubusercontent.com/maja601/EuroCrops/refs/heads/main/csvs/country_mappings/{csv_file}"


def load_ec_mapping(csv_file=None, url=None):
    if not (csv_file or url):
        raise ValueError("Either csv_file or url must be specified")
    if not url:
        url = ec_url(csv_file)
    content = load_file(url)
    return list(csv.DictReader(StringIO(content.decode("utf-8"))))
