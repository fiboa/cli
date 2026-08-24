"""Hilbert-order helpers for the per-file streaming merge.

``PerFileBaseConverter`` was written against a ``vecorel_cli.vecorel.hilbert``
module that is not part of any released vecorel-cli; this module provides the
same two functions on top of geopandas' Hilbert-curve internals. The absolute
values do not matter — only that every part file and the merge use the *same*
deterministic reference grid, which ``crs_total_bounds`` guarantees per CRS.
"""

from __future__ import annotations

import numpy as np

LEVEL = 16  # 2^16 x 2^16 grid, geopandas' default precision


def crs_total_bounds(crs) -> tuple[float, float, float, float]:
    """A fixed (xmin, ymin, xmax, ymax) reference frame for a CRS.

    Uses the CRS's declared area of use, projected into the CRS by sampling
    the area's corners and edge midpoints (projection edges can bow outward).
    Falls back to the full lon/lat world when no area of use is declared.
    """
    from pyproj import CRS, Transformer

    c = CRS.from_user_input(crs)
    aou = c.area_of_use
    if aou is None:
        west, south, east, north = -180.0, -90.0, 180.0, 90.0
    else:
        west, south, east, north = aou.west, aou.south, aou.east, aou.north
    if c.is_geographic:
        return (west, south, east, north)
    t = Transformer.from_crs(c.geodetic_crs, c, always_xy=True)
    lons = np.array([west, (west + east) / 2, east])
    lats = np.array([south, (south + north) / 2, north])
    grid_lon, grid_lat = np.meshgrid(lons, lats)
    xs, ys = t.transform(grid_lon.ravel(), grid_lat.ravel())
    xs = np.asarray(xs)[np.isfinite(xs)]
    ys = np.asarray(ys)[np.isfinite(ys)]
    if xs.size == 0 or ys.size == 0:
        raise ValueError(f"Cannot project the area of use of CRS {crs!r}")
    return (float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max()))


def hilbert_distances_from_bounds(bounds, total_bounds) -> np.ndarray:
    """Hilbert-curve distance of each feature's bbox midpoint.

    ``bounds`` is an (N, 4) array of [xmin, ymin, xmax, ymax]; the reference
    frame ``total_bounds`` must be identical for every file that is merged.
    """
    from geopandas.tools.hilbert_curve import _continuous_to_discrete_coords, _encode

    bounds = np.asarray(bounds, dtype="float64")
    total_bounds = np.asarray(total_bounds, dtype="float64")
    x, y = _continuous_to_discrete_coords(bounds, LEVEL, total_bounds)
    return _encode(LEVEL, x, y)
