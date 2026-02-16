from pathlib import Path

import geopandas
from pytest import mark

from fiboa_cli.improve import ImproveData
from fiboa_cli.validate import ValidateData

files = [
    "fiboa-example.json",
    "improve/be_vlg_2024_fiboa_0_2.parquet",
    "improve/dk_2024_fiboa_0_2.parquet",
]


@mark.parametrize("base", files)
def test_improve_base(tmp_parquet_file, base):
    source = Path("tests/data-files") / base

    # Fiboa-0_2 file is not fiboa or vecorel compliant
    assert ValidateData().validate(source).is_valid() == ("fiboa_0_2" not in base)

    ImproveData().improve_file(source=source, target=tmp_parquet_file)
    result = ValidateData().validate(tmp_parquet_file)
    assert result.is_valid(), result.errors


@mark.parametrize("base,hcat", list(zip(files[1:], ["be_vlg/be_vlg_2021.csv", "dk/dk_2019.csv"])))
def test_improve_hcat(tmp_parquet_file, base, hcat):
    source = Path("tests/data-files") / base
    hcat = "tests/data-files/convert/" + hcat

    ImproveData().improve_file(source=source, target=tmp_parquet_file, add_hcat=hcat)
    result = ValidateData().validate(tmp_parquet_file, num=100)
    assert result.is_valid(), result.errors

    gdf = geopandas.read_parquet(tmp_parquet_file)
    for col in ["hcat:code", "hcat:name", "hcat:name_en"]:
        assert col in gdf.columns

    mapping = dict(gdf[["crop:name", "hcat:name_en"]].values)
    check = {
        "Wintertarwe": "winter wheat",
        "Grasland": "Grassland",
        "Vinterrug": "Winter rye",
        "Lupin": "Sweet lupine",
    }

    count = sum(mapping[k] == v for k, v in check.items() if k in mapping)
    assert count == 2, f"Missing {len(check) - count} of {len(check)} values in {mapping.keys()}"
