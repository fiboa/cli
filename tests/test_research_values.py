"""Values the generic convert test does not check: dates parsed from mixed formats, and
which GloCAB regions an edition keeps with which mapping date."""

import datetime

import pyarrow.parquet as pq
from loguru import logger

from fiboa_cli.convert import ConvertData

FIXTURES = "tests/data-files/convert"


def convert(tmp_parquet_file, converter, folder, *files, **kwargs):
    logger.remove()
    input_files = {f"{FIXTURES}/{folder}/{name}": name for name in files}
    ConvertData(converter).convert(
        target=tmp_parquet_file, cache=f"{FIXTURES}/{folder}", input_files=input_files, **kwargs
    )
    return pq.read_table(tmp_parquet_file).to_pandas().set_index("id")


def test_ecaas_dates_are_month_first(tmp_parquet_file):
    df = convert(
        tmp_parquet_file,
        "ke_ecaas",
        "ke_ecaas",
        "ecaas_geojson_kenya.geojson",
        mapping_file=f"{FIXTURES}/ke_ecaas/crop.csv",
    )
    # the source writes 11/14/2021 and 2/28/2022: month/day/year
    row = df.loc["ad0898f5-caf1-457c-93c8-885615392e83"]
    assert row["planting_date"] == datetime.date(2021, 11, 14)
    assert row["harvest_date"] == datetime.date(2022, 2, 28)
    # ad4bbf18: 12/1/2021 is 1 December, not 12 January
    assert df.loc["ad4bbf18-f796-42f8-9d66-e1fdb56d1b72", "planting_date"] == datetime.date(
        2021, 12, 1
    )
    # ISO dates pass unchanged
    row = df.loc["faf1c636-e855-43f6-adc8-a48ff4e9fea5"]
    assert row["planting_date"] == datetime.date(2021, 7, 29)
    assert row["harvest_date"] == datetime.date(2021, 12, 10)
    # the source's crop name is kept as it is written, next to HCAT
    assert row["crop:name"] == "Irish_Potatoes"
    assert row["hcat:name"] == "potatoes"


def test_glocab_edition_keeps_its_regions_and_months(tmp_parquet_file):
    df = convert(tmp_parquet_file, "glocab", "glocab", "glocab.gpkg", variant="2017")
    months = (
        df.groupby("region")["determination:datetime"]
        .unique()
        .map(lambda dates: [d.strftime("%Y-%m") for d in dates])
    )
    # the fixture also holds Ukraine_D (2016), Russia_E (2018) and Brazil_A (2019)
    assert months.to_dict() == {
        "Ukraine_A": ["2017-03"],
        "USA_E": ["2017-09"],
    }
    assert set(df["admin:country_code"]) == {"UA", "US"}
    # USA_E has 8 ordinary fields and 4 flagged multi-field polygons in the fixture
    assert df.loc[df["region"] == "USA_E", "no_area"].sum() == 4
