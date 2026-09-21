"""Every HCAT name in a mapping table must carry that name's code.

A wrong code is invisible: the file validates, and a crop query quietly returns
another crop. `tests/data-files/hcat3.csv` is the taxonomy, copied from
https://fiboa.org/code/hcat3.csv.
"""

import csv
from pathlib import Path

DATA = Path(__file__).parent / "data-files"

# Rows that are wrong today, recorded so a new mistake still fails. Each is
# tracked in https://github.com/fiboa/cli/issues/304; remove an entry when the
# table it comes from is fixed. Keyed by (name, code) because the same bad pair
# was copied into several tables.
KNOWN_BAD = {
    # the typo is in the taxonomy, which spells it "parsly"; the tables are right
    ("parsley", "3301061227"),
    ("aspargus", "3301200000"),  # taxonomy: asparagus
    ("pistachios", "3303030400"),  # taxonomy: pistachio
    ("flax_fibre", "3301060701"),  # taxonomy: flax_linen
    # name and code are different crops: the codes belong to esparsette and sweet lupins
    ("lupins", "3301020300"),
    ("soybeans", "3301020700"),
    # right name, wrong code
    ("vineyards_wine_vine_rebland_grapes", "3303070000"),  # 3303060000
    ("topinambur_jerusalem_artichoke", "3301290900"),  # 3301180000
    ("iris", "3301082200"),  # 3301082300
    ("lentils", "3301020300"),  # 3301020500
    ("zucchini_courgette", "3301140200"),  # 3301140600, already fixed upstream
}


def read_rows(path):
    for encoding in ("utf-8", "latin-1"):
        try:
            with open(path, encoding=encoding) as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    return []


def test_mapping_tables_agree_with_the_taxonomy():
    taxonomy = {r["HCAT3_name"]: r["HCAT3_code"] for r in read_rows(DATA / "hcat3.csv")}
    assert len(taxonomy) > 300, "the taxonomy fixture looks truncated"

    wrong = []
    for path in sorted(DATA.glob("**/*.csv")):
        if path.name == "hcat3.csv":
            continue
        rows = read_rows(path)
        if not rows or "HCAT3_name" not in rows[0] or "HCAT3_code" not in rows[0]:
            continue
        for row in rows:
            name = (row.get("HCAT3_name") or "").strip()
            code = (row.get("HCAT3_code") or "").strip()
            if (not name and not code) or (name, code) in KNOWN_BAD:
                continue
            where = f"{path.relative_to(DATA)} {row.get('original_code')}"
            if name not in taxonomy:
                wrong.append(f"{where}: {name!r} is not an HCAT class")
            elif taxonomy[name] != code:
                wrong.append(f"{where}: {name} has {code}, the taxonomy says {taxonomy[name]}")

    assert not wrong, "\n".join(wrong)
