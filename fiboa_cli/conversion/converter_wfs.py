import re
from urllib.parse import urlencode

import requests


class WFSConverterMixin:
    """Download a WFS layer in pages of `wfs_page_size` features.

    Every page is a URL of its own and so a file of its own in the cache: an
    interrupted conversion resumes with the missing pages. The number of pages
    is derived from the server, so a changed layer neither drops its tail nor
    requests empty pages.
    """

    wfs_url = None
    # typeNames, outputFormat, filters, sortBy, ... service, version and request are added
    wfs_params = {}
    wfs_version = "2.0.0"
    # Servers silently cap a larger page at their own maximum, so this must not exceed it
    wfs_page_size = 10_000
    # The extension of the cached pages, which picks the reader: "json", "gml", "zip", ...
    wfs_extension = "gml"
    wfs_timeout = 120

    def get_wfs_params(self):
        """The query of the layer; override when it depends on the variant."""
        return self.wfs_params

    def get_wfs_total(self, params):
        """The number of features the query matches."""
        hits = requests.get(
            self.wfs_url, params={**params, "resultType": "hits"}, timeout=self.wfs_timeout
        )
        hits.raise_for_status()
        # numberMatched in WFS 2.0, numberOfFeatures in 1.1. numberReturned is not
        # used: several servers always report it as 0.
        match = re.search(r'(?:numberMatched|numberOfFeatures)="(\d+)"', hits.text)
        if not match:
            raise ValueError(
                f"The WFS does not report the number of features, override get_wfs_total(): {hits.url}"
            )
        return int(match.group(1))

    def get_wfs_file_name(self, start):
        """The name of the cached page that starts at feature `start`."""
        prefix = f"{self.id}_{self.variant}" if self.variant else self.id
        return f"{prefix}_{start}.{self.wfs_extension}"

    def get_urls(self):
        assert self.wfs_url, f"Define {self.__class__.__name__}.wfs_url"
        params = {
            "service": "WFS",
            "version": self.wfs_version,
            "request": "GetFeature",
            **self.get_wfs_params(),
        }
        total = self.get_wfs_total(params)

        # WFS 2.0 renamed maxFeatures to count; startIndex is a vendor parameter before 2.0
        limit = "maxFeatures" if self.wfs_version.startswith("1.") else "count"
        query = urlencode({**params, limit: self.wfs_page_size})
        return {
            f"{self.wfs_url}?{query}&startIndex={start}": self.get_wfs_file_name(start)
            for start in range(0, total, self.wfs_page_size)
        }
