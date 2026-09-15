import csv
import os
from io import StringIO

import requests
from vecorel_cli.vecorel.util import load_file, name_from_uri

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

    def download_files(self, uris, cache_folder=None, **kwargs):
        """Zenodo answers with two Content-Type headers, which the aiohttp client behind
        the base class rejects; requests does not mind, so fetch those here first."""
        _, cache_dir = self.get_cache(cache_folder)
        for uri in uris:
            if "zenodo.org" not in uri:
                continue
            target = os.path.join(cache_dir, name_from_uri(uri))
            if os.path.exists(target) and os.path.getsize(target) > 0:
                continue
            self.info(f"Downloading {uri}")
            with requests.get(uri, stream=True, timeout=300) as response:
                response.raise_for_status()
                # write beside the target, so an interrupted download is not cached
                with open(f"{target}.part", "wb") as file:
                    for chunk in response.iter_content(chunk_size=8 << 20):
                        file.write(chunk)
            os.replace(f"{target}.part", target)
        return super().download_files(uris, cache_folder, **kwargs)


def ec_url(csv_file):
    return f"https://raw.githubusercontent.com/maja601/EuroCrops/refs/heads/main/csvs/country_mappings/{csv_file}"


def load_ec_mapping(csv_file=None, url=None):
    if not (csv_file or url):
        raise ValueError("Either csv_file or url must be specified")
    if not url:
        url = ec_url(csv_file)
    content = load_file(url)
    return list(csv.DictReader(StringIO(content.decode("utf-8"))))
