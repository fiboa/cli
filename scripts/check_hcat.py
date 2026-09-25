"""Check the HCAT mapping tables the converters read online against https://fiboa.org/code/hcat3.csv.

The offline counterpart is tests/test_hcat_codes.py, which only sees the fixtures.
Run with `pixi run check-hcat`; exits non-zero when a row disagrees with the taxonomy.
"""

import csv
import io
import sys
from collections import defaultdict

import requests

from fiboa_cli.converters import Converters
from fiboa_cli.datasets.commons.hcat import AddHCATMixin, hcat_mapping_url

TAXONOMY = "https://fiboa.org/code/hcat3.csv"
_tables = {}


def fetch(url):
    if url not in _tables:
        response = requests.get(url, timeout=60)
        if response.status_code != 200:
            _tables[url] = None
        else:
            try:
                text = response.content.decode("utf-8")
            except UnicodeDecodeError:
                text = response.content.decode("latin-1")
            _tables[url] = list(csv.DictReader(io.StringIO(text)))
    return _tables[url]


def row_key(row):
    return (row.get("original_code") or "").strip() or (row.get("original_name") or "").strip()


def main():
    taxonomy = {r["HCAT3_name"].strip(): r["HCAT3_code"].strip() for r in fetch(TAXONOMY)}
    problems = defaultdict(set)
    unreachable = defaultdict(set)
    converters = Converters()
    for _id in sorted(converters.list_ids()):
        converter = converters.load(_id)
        if not isinstance(converter, AddHCATMixin) or not converter.hcat_mapping_csv:
            continue
        rows = {}
        for url in [converter.hcat_mapping_csv, *converter.hcat_mapping_supplements]:
            table = fetch(hcat_mapping_url(url))
            if table is None:
                unreachable[hcat_mapping_url(url)].add(_id)
                continue
            rows |= {row_key(r): r for r in table}
        for row in rows.values():
            name = (row.get("HCAT3_name") or "").strip()
            code = (row.get("HCAT3_code") or "").strip()
            if not name and not code:
                continue
            if name not in taxonomy:
                problems[f"{name!r} ({code}) is not an HCAT class"].add(_id)
            elif taxonomy[name] != code:
                problems[f"{name} has {code}, the taxonomy says {taxonomy[name]}"].add(_id)

    for url, ids in sorted(unreachable.items()):
        print(f"unreachable: {url} ({', '.join(sorted(ids))})")
    for problem, ids in sorted(problems.items()):
        print(f"{problem}: {', '.join(sorted(ids))}")
    if not problems and not unreachable:
        print("All mapping tables agree with the taxonomy.")
    return 1 if problems or unreachable else 0


if __name__ == "__main__":
    sys.exit(main())
