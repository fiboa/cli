"""Mapping Africa (lacuna_labels): the label catalog decides which labellings are kept and
adds each field's basemap month, class and labeller scores."""

import pyarrow.parquet as pq
from loguru import logger

from fiboa_cli.convert import ConvertData

FIXTURES = "tests/data-files/convert/lacuna_labels"
FILES = ("mapped_fields_final.parquet", "label-catalog-filtered.csv")


def convert(tmp_parquet_file):
    logger.remove()
    ConvertData("lacuna_labels").convert(
        target=tmp_parquet_file,
        cache=FIXTURES,
        input_files={f"{FIXTURES}/{name}": name for name in FILES},
    )
    return pq.read_table(tmp_parquet_file).to_pandas()


def test_only_catalog_labellings_are_kept(tmp_parquet_file):
    df = convert(tmp_parquet_file)
    # the fixture holds 88 fields from 7 labellings of 3 sites; the catalog keeps one per site
    assert df.groupby("site")["assignment_id"].unique().map(list).to_dict() == {
        "AO2878478": [12003],
        "GH0000539": [15037],
        "NA0027035": [38229],
    }
    assert len(df) == 20
    assert df["id"].is_unique


def test_catalog_values_are_joined(tmp_parquet_file):
    df = convert(tmp_parquet_file).set_index("site")
    na = df.loc["NA0027035"].iloc[0]
    # Namibia's code is "NA", which must not be read as a missing value
    assert na["admin:country_code"] == "NA"
    assert na["label_class"] == "1d"
    assert na["labeller"] == "26"
    assert na["determination:datetime"].strftime("%Y-%m") == "2022-06"
    gh = df.loc["GH0000539"].iloc[0]
    assert gh["label_class"] == "2"
    assert round(gh["qscore"], 4) == 0.6368
    assert gh["determination:datetime"].strftime("%Y-%m") == "2018-02"
