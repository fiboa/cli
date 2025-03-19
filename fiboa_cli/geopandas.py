# This file is coming from GeoPandas and is modified to support additional metadata.
# Can be removed once https://github.com/geopandas/geopandas/issues/3182 is fixed.
# Code extracted from commit https://github.com/geopandas/geopandas/tree/80edc868454d3fae943b734ed1719c2197806815

from geopandas._compat import import_optional_dependency
from geopandas.io.arrow import _create_metadata, _encode_metadata, _validate_dataframe
from geopandas.io.file import _expand_user


def _geopandas_to_arrow(df, index=None, schema_version=None, write_covering_bbox=None, schema=None):
    """
    Helper function with main, shared logic for to_parquet/to_feather.
    """
    from pyarrow import StructArray, Table

    _validate_dataframe(df)

    # The following lines can be removed once the following PR is merged and released:
    # https://github.com/geopandas/geopandas/pull/3412
    geometry_encoding = {}
    for col in df.columns[df.dtypes == "geometry"]:
        geometry_encoding[col] = "WKB"

    geo_metadata = _create_metadata(
        df,
        schema_version=schema_version,
        geometry_encoding=geometry_encoding,  # can also be removed then
        write_covering_bbox=write_covering_bbox,
    )

    if any(df[col].array.has_z.any() for col in df.columns[df.dtypes == "geometry"]):
        raise ValueError("Cannot write 3D geometries")

    bounds = (
        df.bounds
    )  # Must be retrieved before we convert to WKB, otherwise there are no bounds left
    df = df.to_wkb()

    table = Table.from_pandas(df, schema=schema, preserve_index=index)

    if write_covering_bbox:
        if "bbox" in df.columns:
            raise ValueError(
                "An existing column 'bbox' already exists in the dataframe. "
                "Please rename to write covering bbox."
            )
        bbox_array = StructArray.from_arrays(
            [bounds["minx"], bounds["miny"], bounds["maxx"], bounds["maxy"]],
            names=["xmin", "ymin", "xmax", "ymax"],
        )
        table = table.append_column("bbox", bbox_array)

    # Store geopandas specific file-level metadata
    # This must be done AFTER creating the table or it is not persisted
    metadata = table.schema.metadata
    metadata.update({b"geo": _encode_metadata(geo_metadata)})
    if schema:
        metadata.update(schema.metadata)

    return table.replace_schema_metadata(metadata)


def to_parquet(
    df,
    path,
    index=None,
    compression="snappy",
    schema_version=None,
    write_covering_bbox=False,
    schema=None,
    **kwargs,
):
    """
    Write a GeoDataFrame to the Parquet format.

    Any geometry columns present are serialized to WKB format in the file.

    Requires 'pyarrow'.

    This is tracking version 1.0.0 of the GeoParquet specification at:
    https://github.com/opengeospatial/geoparquet. Writing older versions is
    supported using the `schema_version` keyword.

    .. versionadded:: 0.8

    Parameters
    ----------
    path : str, path object
    index : bool, default None
        If ``True``, always include the dataframe's index(es) as columns
        in the file output.
        If ``False``, the index(es) will not be written to the file.
        If ``None``, the index(ex) will be included as columns in the file
        output except `RangeIndex` which is stored as metadata only.
    compression : {'snappy', 'gzip', 'brotli', None}, default 'snappy'
        Name of the compression to use. Use ``None`` for no compression.
    schema_version : {'0.1.0', '0.4.0', '1.0.0', None}
        GeoParquet specification version; if not provided will default to
        latest supported version.
    write_covering_bbox : bool, default False
        Writes the bounding box column for each row entry with column
        name 'bbox'. Writing a bbox column can be computationally
        expensive, hence is default setting is False.
    **kwargs
        Additional keyword arguments passed to pyarrow.parquet.write_table().
    """
    parquet = import_optional_dependency(
        "pyarrow.parquet", extra="pyarrow is required for Parquet support."
    )

    path = _expand_user(path)
    table = _geopandas_to_arrow(
        df,
        index=index,
        schema_version=schema_version,
        write_covering_bbox=write_covering_bbox,
        schema=schema,
    )
    parquet.write_table(table, path, compression=compression, **kwargs)
