"""Every HCAT name in a mapping table must carry that name's code.

A wrong code is invisible: the file validates, and a crop query quietly returns
another crop. `tests/data-files/hcat3.csv` is the taxonomy, copied from
https://fiboa.org/code/hcat3.csv. `pixi run check-hcat` runs the same check
against the tables online.
"""

import csv
import os
from pathlib import Path

from fiboa_cli.converters import Converters
from fiboa_cli.datasets.commons.hcat import AddHCATMixin

DATA = Path(__file__).parent / "data-files"


def read_rows(path):
    for encoding in ("utf-8", "latin-1"):
        try:
            with open(path, encoding=encoding) as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    return []


def row_key(row):
    return (row.get("original_code") or "").strip() or (row.get("original_name") or "").strip()


def applied_tables():
    """Per fixture table a converter reads: the rows it applies, supplements winning by code."""
    converters = Converters()
    tables, missing = {}, []
    for _id in converters.list_ids():
        converter = converters.load(_id)
        if not isinstance(converter, AddHCATMixin) or not converter.hcat_mapping_csv:
            continue
        folder = DATA / "convert" / _id
        main = folder / os.path.basename(converter.hcat_mapping_csv)
        if not main.exists():
            continue
        rows = {row_key(r): r for r in read_rows(main)}
        for url in converter.hcat_mapping_supplements:
            supplement = folder / os.path.basename(url)
            if not supplement.exists():
                missing.append(str(supplement.relative_to(DATA)))
                continue
            rows |= {row_key(r): r for r in read_rows(supplement)}
        tables[main] = list(rows.values())
    return tables, missing


def test_mapping_tables_agree_with_the_taxonomy():
    taxonomy = {r["HCAT3_name"]: r["HCAT3_code"] for r in read_rows(DATA / "hcat3.csv")}
    assert len(taxonomy) > 300, "the taxonomy fixture looks truncated"

    applied, missing = applied_tables()
    assert not missing, "supplements without a fixture: " + ", ".join(missing)

    wrong = []
    for path in sorted(DATA.glob("**/*.csv")):
        if path.name == "hcat3.csv":
            continue
        # a table a converter reads is checked as corrected by its supplements
        rows = applied.get(path) or read_rows(path)
        if not rows or "HCAT3_name" not in rows[0] or "HCAT3_code" not in rows[0]:
            continue
        for row in rows:
            name = (row.get("HCAT3_name") or "").strip()
            code = (row.get("HCAT3_code") or "").strip()
            if not name and not code:
                continue
            where = f"{path.relative_to(DATA)} {row.get('original_code')}"
            if name not in taxonomy:
                wrong.append(f"{where}: {name!r} is not an HCAT class")
            elif taxonomy[name] != code:
                wrong.append(f"{where}: {name} has {code}, the taxonomy says {taxonomy[name]}")

    assert not wrong, "\n".join(wrong)
