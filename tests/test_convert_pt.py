"""Checks for PT 2017-2022 that the column expectations in test_convert.py cannot see."""

import glob
import os
import sys
import zipfile
from csv import DictReader
from unittest.mock import patch

import pandas as pd
import pyarrow.parquet as pq
import pyogrio
from loguru import logger
from pytest import fixture, mark, raises

from fiboa_cli.convert import ConvertData
from fiboa_cli.datasets import pt

PT = "tests/data-files/convert/pt"
FIXTURE_ROWS = {"2017": 480, "2018": 385, "2019": 360}
# fields the 2018 fixture has in both Norte_N and Norte_S
DUPLICATED_IN_2018 = 30


def _load_ec(csv_file=None, url=None):
    if csv_file and "://" in csv_file:
        csv_file = csv_file.split("/")[-1]
    path = url if url and "://" not in url else f"{PT}/{csv_file}"
    return list(DictReader(open(path, "r", encoding="utf-8")))


def _convert(target, variant, converter=None, **kwargs):
    # loguru sinks are global, so the sink must not outlive the call
    sink = logger.add(sys.stdout, format="{message}", level="DEBUG", colorize=False)
    try:
        # pt.py imports load_ec_mapping by name, so it is patched in both modules
        with (
            patch("fiboa_cli.datasets.commons.hcat.load_ec_mapping", side_effect=_load_ec),
            patch("fiboa_cli.datasets.pt.load_ec_mapping", side_effect=_load_ec),
        ):
            kwargs.setdefault("cache", PT)
            if converter is None:
                ConvertData("pt").convert(target=target, variant=variant, **kwargs)
            else:
                converter.convert(target, variant=variant, **kwargs)
    finally:
        logger.remove(sink)
    return pq.read_table(target).to_pandas()


def _island_ids(df):
    ids = df["id"].astype("int64")
    return ids[ids >= pt.ISLAND_ID_BASE]


@fixture(scope="module")
def converted(tmp_path_factory):
    out = {}
    for variant in ("2017", "2018", "2019"):
        target = tmp_path_factory.mktemp(variant) / "test.parquet"
        out[variant] = _convert(target, variant)
    return out


@mark.parametrize("variant", ("2017", "2018", "2019"))
def test_ids_are_unique_across_the_edition(converted, variant):
    df = converted[variant]
    # repeated ids would get a ~<n> suffix and show only as extra rows
    assert len(df) == FIXTURE_ROWS[variant]
    assert df["id"].is_unique
    assert not df["id"].astype("string").str.contains("~").any()
    assert df["metrics:area"].notna().all()


def test_2018_drops_exactly_the_duplicated_rows(converted):
    rows_read = sum(
        pyogrio.read_info(f"{PT}/extracted.2018/{m}")["features"] for m in pt.MEMBERS["2018"]
    )
    assert rows_read - len(converted["2018"]) == DUPLICATED_IN_2018


def test_an_undeclared_member_overlap_shows_as_suffixed_ids(tmp_path):
    with patch.dict(pt.OVERLAPPING_MEMBERS, {"2018": (None, None)}):
        df = _convert(tmp_path / "x.parquet", "2018")
    # both copies of each repeated id get a suffix
    assert int(df["id"].astype("string").str.contains("~").sum()) == 2 * DUPLICATED_IN_2018


def test_2017_island_rows_survive_without_a_source_identifier(converted):
    df = converted["2017"]
    islands = sum(
        pyogrio.read_info(f"{PT}/extracted.2017/Ocupacoes_solo_{r}.shp")["features"]
        for r in ("RAA", "RAM")
    )
    synthesised = df["id"].astype("int64") >= pt.ISLAND_ID_BASE
    assert int(synthesised.sum()) == islands
    assert df.loc[synthesised, "id"].is_unique
    assert df.loc[~synthesised, "id"].astype("int64").max() < pt.ISLAND_ID_BASE
    assert (df.loc[synthesised, "crop:code"] == "").all()


def test_2017_island_ids_are_stable_across_runs(tmp_path):
    key = ["block_id", "metrics:area"]
    runs = [_convert(tmp_path / f"{n}.parquet", "2017") for n in ("a", "b")]
    a, b = (df[df["id"].astype("int64") >= pt.ISLAND_ID_BASE].sort_values(key) for df in runs)
    assert a["id"].tolist() == b["id"].tolist()


def test_2017_island_ids_follow_the_declared_sort(converted):
    islands = converted["2017"].loc[_island_ids(converted["2017"]).index].copy()
    islands["n"] = islands["id"].astype("int64") - pt.ISLAND_ID_BASE
    # RAA is numbered first, then RAM; within a file the ids ascend with PAR_NUM
    start = 0
    for region in ("RAA", "RAM"):
        rows = pyogrio.read_info(f"{PT}/extracted.2017/Ocupacoes_solo_{region}.shp")["features"]
        block = islands[(islands["n"] >= start) & (islands["n"] < start + rows)]
        assert len(block) == rows
        assert block.sort_values("n")["block_id"].is_monotonic_increasing
        start += rows


@mark.parametrize(
    "variant,member",
    (
        ("2017", "ocupacoes_solo_norte_n1.shp"),
        ("2018", "ocupacoes.solo.Norte_N1.2018jun10.shp"),
        ("2019", "ocupacoes_solo_n_1.shp"),
    ),
)
def test_projected_members_still_get_an_area(converted, variant, member):
    """The only files published in EPSG:3763; the area is measured after reprojection."""
    assert pyogrio.read_info(f"{PT}/extracted.{variant}/{member}")["crs"] == "EPSG:3763"
    area = converted[variant]["metrics:area"]
    assert area.notna().all()
    # square metres, not hectares or degrees
    assert (area > 10).all()
    assert area.median() > 100


def test_unresolved_question_mark_raises():
    converter = pt.PTConverter()
    converter.variant = "2018"
    converter.ec_mapping = _load_ec("pt.csv")
    with raises(AssertionError, match=r"unknown '\?'"):
        converter._crop_codes(pd.Series(["BATATA", "COURG?TTE"]))


def test_crop_names_resolve_across_the_spellings_2017_uses(converted):
    pairs = converted["2017"][["crop:name", "crop:code"]].drop_duplicates()
    coded = pairs[pairs["crop:code"] != ""]
    assert len(coded[coded["crop:name"].str.contains("_", na=False)]) >= 5
    assert len(coded[coded["crop:name"].str.contains("[ÁÂÃÇÉÊÍÓÔÕÚ]", na=False)]) >= 3
    lookup = dict(zip(coded["crop:name"], coded["crop:code"]))
    assert lookup["PRADOS_TEMPORARIOS"] == lookup["PRADOS TEMPORÁRIOS"]


def test_2018_question_mark_names_survive_the_whole_pipeline(converted):
    """They are all in Norte_N1, whose crop columns are lowercase and skip c8."""
    df = converted["2018"]
    q = df[df["crop:name"].str.contains(r"\?", na=False)]
    assert len(q) > 0
    assert (q["crop:code"] != "").all()
    assert q["hcat:code"].notna().all()


@mark.parametrize("variant", ("2017", "2018", "2019"))
def test_block_id_is_an_integer(converted, variant):
    df = converted[variant]
    assert str(df["block_id"].dtype) in ("Int64", "int64")
    assert df["block_id"].min() > 10**11


def test_2022_extracts_the_deflate64_archive(tmp_path):
    """The published 2017-2022 archives are Deflate64, and so is this fixture."""
    archive = f"{PT}/2022.zip"
    with zipfile.ZipFile(archive) as zf:
        assert {info.compress_type for info in zf.infolist()} == {9}
    # an empty cache, so the archive is extracted
    df = _convert(
        tmp_path / "out.parquet",
        "2022",
        cache=str(tmp_path),
        input_files={archive: pt.MEMBERS["2022"]},
    )
    assert len(df) == 400


def _fixture_crop_codes(year, folder):
    """Each field's crop code, looked up in the crop table without the converter."""
    with zipfile.ZipFile(f"{PT}/{year}.zip") as zf:
        zf.extractall(folder)
    ids = pd.concat(
        pyogrio.read_dataframe(path, columns=["OSA_ID"], read_geometry=False)["OSA_ID"]
        for pattern in pt.MEMBERS[year]
        for path in glob.glob(os.path.join(folder, "**", pattern), recursive=True)
    ).astype("int64")
    (table,) = glob.glob(os.path.join(folder, "**", pt.CROP_TABLE[year]), recursive=True)
    key = next(f for f in pyogrio.read_info(table)["fields"] if f.lower() == "osa_id")
    crops = pyogrio.read_dataframe(table, columns=[key, "C1"], read_geometry=False)
    crops = crops[crops[key] != 0]
    codes = ids.map(crops.set_index(crops[key].astype("int64"))["C1"]).fillna("")
    return dict(zip(ids, codes))


@mark.parametrize("year", ("2020", "2021"))
def test_crop_codes_are_joined_from_the_crop_table(tmp_path, year):
    expected = _fixture_crop_codes(year, tmp_path / "source")
    assert any(expected.values()) and not all(expected.values())
    df = _convert(tmp_path / "out.parquet", year)
    assert dict(zip(df["id"].astype("int64"), df["crop:code"])) == expected


def test_a_reused_converter_starts_each_edition_afresh(tmp_path):
    converter = pt.PTConverter()
    _convert(tmp_path / "2020.parquet", "2020", converter=converter)
    reused = _convert(tmp_path / "2021.parquet", "2021", converter=converter)
    fresh = _convert(tmp_path / "2021_fresh.parquet", "2021")
    key = ["id", "crop:code"]
    assert reused[key].sort_values("id").values.tolist() == (
        fresh[key].sort_values("id").values.tolist()
    )

    first = _convert(tmp_path / "a.parquet", "2017", converter=converter)
    second = _convert(tmp_path / "b.parquet", "2017", converter=converter)
    assert sorted(_island_ids(first)) == sorted(_island_ids(second))
