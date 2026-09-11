import json

import pyarrow.parquet as pq
import shapely

from fiboa_cli.conversion.fiboa_converter import FiboaBaseConverter
from fiboa_cli.datasets.jp import JPConverter
from fiboa_cli.validate import ValidateData

# A GeoDataFrame-based twin of the DuckDB-based jp converter, built from the
# same configuration so that the two codepaths cannot drift apart.
SHARED_ATTRIBUTES = (
    "id",
    "short_name",
    "title",
    "description",
    "provider",
    "attribution",
    "license",
    "variants",
    "columns",
    "column_additions",
    "missing_schemas",
)
PandasJPConverter = type(
    "PandasJPConverter",
    (FiboaBaseConverter,),
    {key: getattr(JPConverter, key) for key in SHARED_ATTRIBUTES},
)


def test_jp_codepath_parity(tmp_folder):
    """The DuckDB-based jp converter and its GeoDataFrame-based twin must
    produce comparable files: same schema, same rows in the same order,
    same key metadata, same packaging."""
    kwargs = {"variant": "test", "compression": "zstd", "geoparquet_version": "1.1.0"}
    pandas_dest = tmp_folder / "pandas.parquet"
    duckdb_dest = tmp_folder / "duckdb.parquet"
    PandasJPConverter().convert(pandas_dest, **kwargs)
    JPConverter().convert(duckdb_dest, **kwargs)

    with pq.ParquetFile(pandas_dest) as pf:
        pandas_schema = pf.schema_arrow
        pandas_table = pf.read()
        pandas_groups = pf.metadata.num_row_groups
        pandas_compression = pf.metadata.row_group(0).column(0).compression
    with pq.ParquetFile(duckdb_dest) as pf:
        duckdb_schema = pf.schema_arrow
        duckdb_table = pf.read()
        duckdb_groups = pf.metadata.num_row_groups
        duckdb_compression = pf.metadata.row_group(0).column(0).compression

    # Same columns with the same types and nullability (the column order is
    # allowed to differ)
    assert sorted(pandas_schema.names) == sorted(duckdb_schema.names)
    for name in pandas_schema.names:
        f1, f2 = pandas_schema.field(name), duckdb_schema.field(name)
        assert f1.type == f2.type, f"{name}: {f1.type} != {f2.type}"
        assert f1.nullable == f2.nullable, f"{name}: nullability differs"

    # Same rows in the same order: both codepaths sort against the same Hilbert
    # grid and resolve ties by source order. The geometries must describe the
    # same shapes, but the WKB may differ in vertex order (different GEOS builds)
    assert pandas_table.num_rows == duckdb_table.num_rows
    for column in pandas_schema.names:
        if column in ("geometry", "bbox"):
            continue
        assert pandas_table[column].to_pylist() == duckdb_table[column].to_pylist(), (
            f"{column}: values differ"
        )
    pandas_geoms = shapely.from_wkb(pandas_table["geometry"].to_pylist())
    duckdb_geoms = shapely.from_wkb(duckdb_table["geometry"].to_pylist())
    for g1, g2 in zip(pandas_geoms, duckdb_geoms):
        assert shapely.equals(g1, g2)

    # Same collection metadata and the same key GeoParquet metadata
    pandas_collection = json.loads(pandas_schema.metadata[b"collection"])
    duckdb_collection = json.loads(duckdb_schema.metadata[b"collection"])
    assert pandas_collection == duckdb_collection

    pandas_geo = json.loads(pandas_schema.metadata[b"geo"])
    duckdb_geo = json.loads(duckdb_schema.metadata[b"geo"])
    for key in ("version", "primary_column"):
        assert pandas_geo[key] == duckdb_geo[key]
    pandas_column = pandas_geo["columns"]["geometry"]
    duckdb_column = duckdb_geo["columns"]["geometry"]
    for key in ("encoding", "covering", "crs", "bbox"):
        assert pandas_column.get(key) == duckdb_column.get(key), f"geo {key} differs"
    assert sorted(pandas_column.get("geometry_types", [])) == sorted(
        duckdb_column.get("geometry_types", [])
    )

    # Same packaging
    assert pandas_compression == duckdb_compression
    assert pandas_groups == duckdb_groups

    # Both validate
    for dest in (pandas_dest, duckdb_dest):
        validation = ValidateData().validate(dest, num=100, schema_map={})
        assert validation.errors == []
