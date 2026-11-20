"""RPG 4.0 (the 2024 edition): three volumes, RPG_Parcelles.gpkg, lowercase columns, and parcel ids the
source issues more than once. The fixture is 100 rows of the real file: the five parcels that share id
11036490, two with surf_parc 0 and 93 others."""

from csv import DictReader
from unittest.mock import patch

import pyarrow.parquet as pq

from fiboa_cli.convert import ConvertData

FIXTURES = "tests/data-files/convert/fr"


def fixture_table(csv_file=None, url=None):
    with open(f"{FIXTURES}/fr.csv", encoding="utf-8") as f:
        return list(DictReader(f))


@patch("fiboa_cli.datasets.commons.hcat.load_hcat_mapping", side_effect=fixture_table)
def test_rpg_4_0(_, tmp_parquet_file):
    ConvertData("fr").convert(target=tmp_parquet_file, cache=FIXTURES, variant="2024")
    df = pq.read_table(tmp_parquet_file).to_pandas()

    assert len(df) == 98, "the two parcels with surf_parc 0 are left out"
    assert df["id"].is_unique
    repeated = df.loc[df["parcel_id"] == "11036490", "id"]
    assert sorted(repeated) == [f"11036490~{n}" for n in range(1, 6)]
    assert (df["parcel_id"] == df["id"].str.split("~").str[0]).all()
    assert df["metrics:area"].gt(0).all() and df["crop:code"].notna().all()
    # every code of the fixture is in the table except PHF and MDI, new in RPG 4.0
    assert set(df.loc[df["hcat:code"].isna(), "crop:code"]) == {"PHF", "MDI"}
    assert df["crop:name"].notna().sum() == df["hcat:code"].notna().sum()
