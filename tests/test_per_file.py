import sqlite3
import zipfile

import geopandas as gpd

from fiboa_cli.converters import Converters

FIXTURE = "tests/data-files/convert/es/1501_ALAVA_cd_2025_20250105.gpkg.zip"


def _as_province(tmp_path, code):
    """The fixture's GeoPackage, moved to another province, as a zip of its own."""
    with zipfile.ZipFile(FIXTURE) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".gpkg"))
        gpkg = archive.extract(name, tmp_path / "extracted")
    with sqlite3.connect(gpkg) as db:
        # the spatial index triggers call SpatiaLite functions that plain sqlite3 lacks
        triggers = db.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'").fetchall()
        for (trigger,) in triggers:
            db.execute(f'DROP TRIGGER "{trigger}"')
        db.execute("UPDATE cultivo_declarado SET provincia = ?", (code,))
    copy = tmp_path / f"province_{code}.gpkg.zip"
    with zipfile.ZipFile(copy, "w") as archive:
        archive.write(gpkg, name)
    return copy


def test_each_source_is_converted_on_its_own_and_merged(tmp_path):
    from fiboa_cli import Registry  # noqa

    copy = _as_province(tmp_path, 5)
    output = tmp_path / "es.parquet"

    Converters().load("es").convert(
        str(output), input_files={FIXTURE: ["*.gpkg"], str(copy): ["*.gpkg"]}
    )

    merged = gpd.read_parquet(output)
    assert len(merged) == 20  # 10 rows per source
    assert merged["id"].is_unique
    # constant within each part, so it only survives the merge as a column
    assert sorted(merged["admin_province_code"].unique()) == ["01", "05"]
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(
        ["es.parquet", "extracted", copy.name]
    )  # the parts are gone
