import shutil

import geopandas as gpd

from fiboa_cli.converters import Converters

FIXTURE = "tests/data-files/convert/es/1501_ALAVA_cd_2025_20250105.gpkg.zip"


def test_each_source_is_converted_on_its_own_and_merged(tmp_path):
    from fiboa_cli import Registry  # noqa

    copy = tmp_path / "copy.gpkg.zip"
    shutil.copy(FIXTURE, copy)
    output = tmp_path / "es.parquet"

    Converters().load("es").convert(
        str(output), input_files={FIXTURE: ["*.gpkg"], str(copy): ["*.gpkg"]}
    )

    merged = gpd.read_parquet(output)
    assert len(merged) == 20  # 10 rows per source
    assert merged["id"].is_unique
    assert set(tmp_path.iterdir()) == {copy, output}  # the parts are gone
