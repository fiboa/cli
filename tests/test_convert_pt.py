"""Edition-specific guards for the Portuguese 2017-2019 backfill.

`test_convert.py` proves each edition converts and delivers its columns. These cover the
three things that are specific to 2017-2019 and that a column list cannot see: the 2018
edition ships one region twice, 2017 ships two files with no identifier at all, and the
northern files are the only ones published in a projected CRS.
"""

import sys
import zipfile
from csv import DictReader
from unittest.mock import patch

import pyarrow.parquet as pq
import pyogrio
from loguru import logger
from pytest import fixture, mark, raises

from fiboa_cli.convert import ConvertData

PT = "tests/data-files/convert/pt"


def _load_ec(csv_file=None, url=None):
    if csv_file and "://" in csv_file:
        csv_file = csv_file.split("/")[-1]
    path = url if url and "://" not in url else f"{PT}/{csv_file}"
    return list(DictReader(open(path, "r", encoding="utf-8")))


def _convert(target, variant, **kwargs):
    # The converter logs through loguru, whose sinks are global. Binding one to this
    # test's sys.stdout would outlive the test and swallow another module's output, so
    # the sink is added and removed around the call. (test_converters asserts on captured
    # output and fails if a stale sink is left behind.)
    sink = logger.add(sys.stdout, format="{message}", level="DEBUG", colorize=False)
    try:
        # AddHCATMixin calls commons.hcat.load_ec_mapping, and pt.py imports it by name
        # for its own crop name lookup, so both are pinned to the committed pt.csv.
        with (
            patch("fiboa_cli.datasets.commons.hcat.load_ec_mapping", side_effect=_load_ec),
            patch("fiboa_cli.datasets.pt.load_ec_mapping", side_effect=_load_ec),
        ):
            kwargs.setdefault("cache", PT)
            ConvertData("pt").convert(target=target, variant=variant, **kwargs)
    finally:
        logger.remove(sink)
    return pq.read_table(target).to_pandas()


@fixture(scope="module")
def converted(tmp_path_factory):
    out = {}
    for variant in ("2017", "2018", "2019"):
        target = tmp_path_factory.mktemp(variant) / "test.parquet"
        out[variant] = _convert(target, variant)
    return out


# The fixture keeps 100 features of Norte_N and 100 of Norte_S, of which 30 carry an
# OSA_ID that appears in both, mirroring the 154,980 the real edition repeats.
FIXTURE_ROWS = {"2017": 480, "2018": 385, "2019": 360}
DUPLICATED_IN_2018 = 30


@mark.parametrize("variant", ("2017", "2018", "2019"))
def test_ids_are_unique_across_the_edition(converted, variant):
    """2018's Norte_S repeats 154,980 of Norte_N's fields, exactly.

    Same OSA_ID, same PAR_NUM, same crop, geometry equal to 1e-9. Converting both members
    as published inflates the edition by that many field boundaries, and nothing else in
    the pipeline would notice: the rows are individually valid.
    """
    df = converted[variant]
    # One row per source feature, multipart fields included. A distinct-id count alone
    # would not do: the base converter gives a repeated id a ~<n> suffix, so duplicates
    # reach the output as unique ids and show up only as extra rows and the suffix.
    assert len(df) == FIXTURE_ROWS[variant], (
        f"{variant}: {len(df)} rows, expected {FIXTURE_ROWS[variant]}"
    )
    assert df["id"].is_unique
    assert not df["id"].astype("string").str.contains("~").any()
    # Every id that survives must carry a geometry and a measured area.
    assert df["metrics:area"].notna().all()


def test_2018_drops_exactly_the_duplicated_rows(converted):
    """The count is the test: 30 of the fixture's 415 rows are the Norte_N/Norte_S repeat."""
    rows_read = sum(
        pyogrio.read_info(f"{PT}/extracted.2018/{m}")["features"]
        for m in (
            "Ocupacoes_solo_AML.shp",
            "Ocupacoes_solo_Alentejo.shp",
            "Ocupacoes_solo_Algarve.shp",
            "Ocupacoes_solo_Centro_N.shp",
            "Ocupacoes_solo_Centro_S.shp",
            "Ocupacoes_solo_Norte_N.shp",
            "Ocupacoes_solo_Norte_S.shp",
            "Ocupacoes_solo_RAA.shp",
            "Ocupacoes_solo_RAM.shp",
            "ocupacoes.solo.Norte_N1.2018jun10.shp",
        )
    )
    assert rows_read - len(converted["2018"]) == DUPLICATED_IN_2018


def test_2017_island_rows_survive_without_a_source_identifier(converted):
    """RAA and RAM publish no OSA_ID and repeat PAR_NUM, so the id has to be synthesised.

    They are 177,614 real field boundaries in the full edition and FTW-V2 training data;
    dropping them for want of a key the provider never wrote would be the wrong trade.
    """
    from fiboa_cli.datasets.pt import ISLAND_ID_BASE

    df = converted["2017"]
    islands = sum(
        pyogrio.read_info(f"{PT}/extracted.2017/Ocupacoes_solo_{r}.shp")["features"]
        for r in ("RAA", "RAM")
    )
    synthesised = df["id"].astype("int64") >= ISLAND_ID_BASE
    assert int(synthesised.sum()) == islands
    assert df.loc[synthesised, "id"].is_unique
    # A synthesised id must never be mistakable for a published one.
    assert df.loc[~synthesised, "id"].astype("int64").max() < ISLAND_ID_BASE
    # No crop was published for them, so the code is empty rather than invented.
    assert (df.loc[synthesised, "crop:code"] == "").all()


def test_2017_island_ids_are_stable_across_runs(tmp_path):
    """The sort is the whole guarantee: re-running must not renumber the islands."""
    from fiboa_cli.datasets.pt import ISLAND_ID_BASE

    first = _convert(tmp_path / "a.parquet", "2017")
    second = _convert(tmp_path / "b.parquet", "2017")
    key = ["block_id", "metrics:area"]
    a = first[first["id"].astype("int64") >= ISLAND_ID_BASE].sort_values(key)
    b = second[second["id"].astype("int64") >= ISLAND_ID_BASE].sort_values(key)
    assert a["id"].tolist() == b["id"].tolist()


@mark.parametrize(
    "variant,member",
    (
        ("2017", "ocupacoes_solo_norte_n1.shp"),
        ("2018", "ocupacoes.solo.Norte_N1.2018jun10.shp"),
        ("2019", "ocupacoes_solo_n_1.shp"),
    ),
)
def test_projected_members_still_get_an_area(converted, variant, member):
    """metrics:area is measured, never read, and the northern files are the hard case.

    They are the only members published in ETRS89 / Portugal TM06 rather than WGS 84, and
    the branch in migrate that measures area only fires for a geographic CRS. It works
    because file_migration reprojects each file before the concat, so by the time migrate
    runs the frame is WGS 84 -- but that is an ordering dependency, not an obvious one.

    Three of the thirty source files do publish an area and they disagree on units: 2017's
    RAA and RAM give square metres, 2018's Norte_N1 gives hectares. All of them are
    ignored.
    """
    info = pyogrio.read_info(f"{PT}/extracted.{variant}/{member}")
    assert info["crs"] == "EPSG:3763", f"{member} is no longer the projected case"

    df = converted[variant]
    area = df["metrics:area"]
    assert area.notna().all()
    # Square metres, not hectares and not degrees: a field is bigger than 10 m2, and the
    # smallest of these is nowhere near the 1e-8 that measuring in degrees would give.
    assert (area > 10).all()
    assert area.median() > 100


def test_unresolved_question_mark_raises():
    """2018 lost accents from some crop names, leaving "FEIJ?O" for "FEIJÃO".

    The fourteen that occur were resolved offline, each to exactly one pt.csv entry, and
    hard-coded. A new one must stop the conversion rather than quietly produce a field
    with no crop code, because a "?" name is unrecoverable at runtime.
    """
    from fiboa_cli.datasets import pt

    converter = pt.PTConverter()
    converter.variant = "2018"
    converter.ec_mapping = _load_ec("pt.csv")
    import pandas as pd

    with raises(AssertionError, match=r"unknown '\?'"):
        converter._crop_codes(pd.Series(["BATATA", "COURG?TTE"]))


def test_crop_names_resolve_across_the_spellings_2017_uses(converted):
    """2017 spells one crop four ways inside a single campaign.

    PASTAGENS_ARBUSTIVAS and PASTAGENS ARBUSTIVAS, PRADOS_TEMPORARIOS and PRADOS
    TEMPORÁRIOS. Exact matching against pt.csv resolves 60.70% of the edition's rows;
    folding separators and accents takes it to 98.85%. Both spellings have to land on the
    same code, or the edition splits one crop in two.
    """
    df = converted["2017"]
    pairs = df[["crop:name", "crop:code"]].drop_duplicates()
    coded = pairs[pairs["crop:code"] != ""]

    underscored = coded[coded["crop:name"].str.contains("_", na=False)]
    assert len(underscored) >= 5, (
        "no underscore-spelled name resolved to a code; the separator fold is not working"
    )
    accented = coded[coded["crop:name"].str.contains("[ÁÂÃÇÉÊÍÓÔÕÚ]", regex=True, na=False)]
    assert len(accented) >= 3, "no accented name resolved to a code; the accent fold is not working"
    # The two spellings of one crop must agree on the code, not merely both have one.
    lookup = dict(zip(coded["crop:name"], coded["crop:code"]))
    underscored_code = lookup.get("PRADOS_TEMPORARIOS")
    assert underscored_code is not None
    assert underscored_code == lookup.get("PRADOS TEMPORÁRIOS")


def test_2018_question_mark_names_survive_the_whole_pipeline(converted):
    """End-to-end cover for the one member that is awkward in three ways at once.

    Every '?' name in 2018 lives in ocupacoes.solo.Norte_N1.2018jun10, which is also the
    only file whose crop columns are lowercase and non-contiguous (c1..c7, c9) and one of
    the two published in EPSG:3763. A converter that matched crop columns case-sensitively,
    or assumed the primary one is spelled "C1", would read no crop from it at all and the
    column-level tests would still pass, because nine other members supply crop:code.
    """
    df = converted["2018"]
    q = df[df["crop:name"].str.contains(r"\?", regex=True, na=False)]
    assert len(q) > 0, "the fixture no longer carries any '?' name"
    assert (q["crop:code"] != "").all(), (
        f"{int((q['crop:code'] == '').sum())} '?' row(s) reached the output without a code"
    )
    assert q["hcat:code"].notna().all()
    # Resolved to a code, but the published name is left exactly as the provider wrote it.
    assert q["crop:name"].str.contains(r"\?", regex=True).all()


@mark.parametrize("variant", ("2017", "2018", "2019"))
def test_block_id_is_an_integer(converted, variant):
    """PAR_NUM is a 13-digit numeric string, and block_id is declared int64.

    Passed through as a string it validates, stays unique and is silently the wrong type.
    """
    df = converted[variant]
    assert str(df["block_id"].dtype) in ("Int64", "int64"), (
        f"{variant}: block_id is {df['block_id'].dtype}, expected an integer type"
    )
    assert df["block_id"].min() > 10**11


def test_2017_island_ids_follow_the_declared_sort(converted):
    """The ids are positions in a stated order, so the order itself is the contract.

    Assigning them in file order instead would still be unique and still be stable, and
    nothing downstream would notice until the source file was re-cut.
    """
    from fiboa_cli.datasets.pt import ISLAND_ID_BASE

    df = converted["2017"]
    islands = df[df["id"].astype("int64") >= ISLAND_ID_BASE].copy()
    islands["n"] = islands["id"].astype("int64") - ISLAND_ID_BASE

    # The files are numbered one after another in MEMBERS order, so the boundary between
    # them is the row count of the first. Within one file the ids ascend with PAR_NUM,
    # because PAR_NUM is the first sort key; across files they simply continue.
    start = 0
    for region in ("RAA", "RAM"):
        rows = pyogrio.read_info(f"{PT}/extracted.2017/Ocupacoes_solo_{region}.shp")["features"]
        block = islands[(islands["n"] >= start) & (islands["n"] < start + rows)]
        assert len(block) == rows, f"{region}: {len(block)} ids in its range, expected {rows}"
        ordered = block.sort_values("n")
        assert ordered["block_id"].is_monotonic_increasing, (
            f"{region}: island ids do not ascend with PAR_NUM, so they were not assigned "
            f"under the (PAR_NUM, x, y) sort that _island_ids documents"
        )
        start += rows


def test_an_undeclared_member_overlap_shows_as_suffixed_ids(tmp_path):
    """Without OVERLAPPING_MEMBERS the repeated fields are published twice, and the base
    converter numbers both copies (id~1, id~2) rather than failing."""
    from fiboa_cli.datasets import pt

    with patch.dict(pt.OVERLAPPING_MEMBERS, {"2018": (None, None)}):
        df = _convert(tmp_path / "x.parquet", "2018")
    suffixed = df["id"].astype("string").str.contains("~")
    assert int(suffixed.sum()) == 2 * DUPLICATED_IN_2018


def test_2022_extracts_the_deflate64_archive(tmp_path):
    """IFAP compresses the 2017-2022 archives with Deflate64, which python's zipfile cannot
    read, so the 2022 fixture is Deflate64 too (see to_deflate64.py). The cache is empty,
    so the archive is extracted rather than read from an earlier run's extracted folder."""
    from fiboa_cli.datasets.pt import MEMBERS

    archive = f"{PT}/2022.zip"
    with zipfile.ZipFile(archive) as zf:
        assert {info.compress_type for info in zf.infolist()} == {9}

    df = _convert(
        tmp_path / "out.parquet",
        "2022",
        cache=str(tmp_path),
        input_files={archive: MEMBERS["2022"]},
    )
    assert len(df) == 400
