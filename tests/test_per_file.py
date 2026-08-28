"""Tests for the per-file streaming merge (PerFileBaseConverter) and its
Hilbert-order helpers."""

import shutil
from csv import DictReader
from unittest.mock import patch

import numpy as np
import pyarrow.parquet as pq
import pytest

from fiboa_cli import Registry  # noqa: F401
from fiboa_cli.conversion.hilbert import crs_total_bounds, hilbert_distances_from_bounds
from fiboa_cli.convert import ConvertData
from fiboa_cli.datasets.es import Converter as ESConverter

test_path = "tests/data-files/convert/es"
ZIP = f"{test_path}/1501_ALAVA_cd_2025_20250105.gpkg.zip"


def load_ec(csv_file=None, url=None):
    return list(DictReader(open(f"{test_path}/es.csv", encoding="utf-8")))


def convert_es(target, input_files, cache=test_path):
    with (
        patch("fiboa_cli.datasets.commons.ec.load_ec_mapping", side_effect=load_ec),
        patch("fiboa_cli.datasets.commons.hcat.load_ec_mapping", side_effect=load_ec),
    ):
        ConvertData("es").convert(target=target, cache=cache, input_files=input_files)


# ---------- hilbert helpers ----------


def test_crs_total_bounds_geographic():
    assert crs_total_bounds("EPSG:4326") == (-180.0, -90.0, 180.0, 90.0)


def test_crs_total_bounds_projected_metric():
    xmin, ymin, xmax, ymax = crs_total_bounds("EPSG:2056")  # Swiss LV95
    assert xmax > xmin and ymax > ymin
    # the Swiss area of use projects to coordinates around (2.6e6, 1.2e6)
    assert 2.0e6 < (xmin + xmax) / 2 < 3.2e6


def test_crs_total_bounds_is_deterministic():
    assert crs_total_bounds("EPSG:3067") == crs_total_bounds("EPSG:3067")


def test_hilbert_distances_locality():
    total = (0.0, 0.0, 100.0, 100.0)
    # three features: two neighbours and one far away
    bounds = np.array(
        [
            [1, 1, 2, 2],
            [2, 1, 3, 2],
            [90, 90, 95, 95],
        ],
        dtype="float64",
    )
    d = hilbert_distances_from_bounds(bounds, total)
    assert len(d) == 3
    assert len(set(d.tolist())) == 3
    # neighbours are closer along the curve than the far-away feature
    assert abs(int(d[0]) - int(d[1])) < abs(int(d[0]) - int(d[2]))


# ---------- PerFileBaseConverter ----------


def test_single_source_degenerates_to_plain_convert(tmp_path, capsys):
    out = tmp_path / "es.parquet"
    convert_es(out, {ZIP: ["*.gpkg"]})
    assert out.exists()
    assert not list(tmp_path.glob("*_part.parquet"))


def test_multi_source_merges_and_cleans_parts(tmp_path, capsys):
    # two sources: the fixture zip under two names
    zip2 = tmp_path / "1502_COPY_cd_2025_20250105.gpkg.zip"
    shutil.copy(ZIP, zip2)
    out = tmp_path / "es.parquet"
    convert_es(out, {ZIP: ["*.gpkg"], str(zip2): ["*.gpkg"]}, cache=str(tmp_path / "cache"))
    assert out.exists()
    n = pq.ParquetFile(out).metadata.num_rows
    assert n == 20  # 10 rows per copy of the fixture
    # parts are removed after a successful merge
    assert not list(out.parent.glob("*_part.parquet"))
    # merged output keeps the geo metadata
    import json

    geo = json.loads(pq.ParquetFile(out).schema_arrow.metadata[b"geo"])
    assert geo["primary_column"] == "geometry"


def _make_part(tmp_path, name="part_a.parquet"):
    out = tmp_path / name
    convert_es(out, {ZIP: ["*.gpkg"]})
    return out


def test_merge_files_rejects_empty_and_bad_version(tmp_path):
    conv = ESConverter()
    with pytest.raises(ValueError, match="No paths"):
        conv.merge_files(str(tmp_path / "o.parquet"), [])
    part = _make_part(tmp_path)
    with pytest.raises(ValueError, match="geoparquet_version"):
        conv.merge_files(str(tmp_path / "o.parquet"), [str(part)], geoparquet_version="9.9.9")


def test_merge_files_rejects_non_geoparquet(tmp_path):
    import pyarrow as pa

    plain = tmp_path / "plain.parquet"
    pq.write_table(pa.table({"a": [1, 2]}), plain)
    conv = ESConverter()
    with pytest.raises(ValueError, match="no 'geo' metadata"):
        conv.merge_files(str(tmp_path / "o.parquet"), [str(plain)])


def test_merge_files_rejects_schema_mismatch(tmp_path):
    part = _make_part(tmp_path)
    # a second file with an extra column
    tbl = pq.read_table(part)
    import pyarrow as pa

    other = tmp_path / "other.parquet"
    tbl2 = tbl.append_column("extra", pa.array([1] * tbl.num_rows))
    schema = tbl2.schema.with_metadata(tbl.schema.metadata)
    pq.write_table(tbl2.cast(schema), other)
    conv = ESConverter()
    with pytest.raises(ValueError, match="Schema mismatch"):
        conv.merge_files(str(tmp_path / "o.parquet"), [str(part), str(other)])


def test_merge_resorts_unsorted_part(tmp_path, capsys):
    part = _make_part(tmp_path)
    # destroy the Hilbert order of a copy: reverse the row order
    shuffled = tmp_path / "part_b.parquet"
    tbl = pq.read_table(part)
    rev = tbl.take(list(reversed(range(tbl.num_rows))))
    pq.write_table(rev.cast(tbl.schema), shuffled)
    conv = ESConverter()
    merged = tmp_path / "merged.parquet"
    conv.merge_files(str(merged), [str(part), str(shuffled)], cleanup_parts=True)
    assert pq.ParquetFile(merged).metadata.num_rows == 2 * tbl.num_rows
    assert not part.exists() and not shuffled.exists()
    # the merged file is globally Hilbert-sorted
    from fiboa_cli.conversion.per_file import _bounds_array_for_table

    out_tbl = pq.read_table(merged)
    keys = hilbert_distances_from_bounds(
        _bounds_array_for_table(out_tbl, "geometry"), crs_total_bounds("EPSG:4258")
    )
    assert (np.diff(keys.astype("int64")) >= 0).all()


def test_bounds_array_wkb_fallback(tmp_path):
    # without a bbox covering column the bounds are decoded from WKB
    part = _make_part(tmp_path)
    tbl = pq.read_table(part)
    if "bbox" in tbl.column_names:
        tbl = tbl.drop_columns(["bbox"])
    from fiboa_cli.conversion.per_file import _bounds_array_for_table

    bounds = _bounds_array_for_table(tbl, "geometry")
    assert bounds.shape == (tbl.num_rows, 4)
    assert (bounds[:, 2] >= bounds[:, 0]).all() and (bounds[:, 3] >= bounds[:, 1]).all()
