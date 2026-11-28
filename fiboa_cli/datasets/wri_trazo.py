import os
import re

import numpy as np
import pandas as pd
import shapely

from ..conversion.fiboa_converter import EQUAL_AREA_CRS, FiboaBaseConverter

BUCKET = "https://data.source.coop/wri-data-lab/trazoannotations"

# Folder -> (year in the file name, basemap the annotators drew on), from each folder's
# "annotation info.txt": "Planet Labs Trainable: No" means a Sentinel-2 basemap
REGIONS = {
    "acre": (2020, "planet"),
    "altoparana": (2020, "planet"),
    "araucaria": (2023, "planet"),
    "caatinga": (2021, "planet"),
    "cerrado": (2021, "planet"),
    "chaco": (2020, "planet"),
    "chiquitania": (2020, "sentinel-2"),
    "humidchaco": (2022, "planet"),
    "lowmonte": (2023, "planet"),
    "maparaguay": (2024, "planet"),
    "matogrosso": (2020, "sentinel-2"),
    "matogrosso_brazil_confidences": (2020, "planet"),
    "matogrosso_brazil_lcdi": (2020, "planet"),
    "matogrosso_brazil_lcdib": (2020, "planet"),
    "matogrosso_brazil_lowconfidences": (2020, "planet"),
    "pampas": (2021, "planet"),
    "pantanal": (2023, "planet"),
    "para": (2020, "sentinel-2"),
    "peruvianamazon": (2022, "planet"),
    "rondonia": (2022, "planet"),
    "testchiquitania": (2020, "planet"),
    "testmatogrosso": (2020, "planet"),
    "testsoy": (2020, "planet"),
    "tocantins": (2024, "planet"),
    "uruguayansavannah": (2020, "planet"),
}
FILE_NAME = re.compile(r"^(?P<region>.+)Annotations_(?P<year>\d{4})\.gpkg$")

# Where regions annotated the same chips, the fields of the region with the higher rank give way
# (the others have rank 1). The test regions stay whole, so that no test field is also in train.
# The chips of the active learning samples confidences and lowconfidences (low model confidence
# on farmland and anywhere) overlap in places and are drawn in as much detail there; which of
# them gives way is a choice.
RANK = {
    "testchiquitania": 0,
    "testmatogrosso": 0,
    "testsoy": 0,
    "matogrosso_brazil_lowconfidences": 2,
}
# A field is "inside" another when this share of its area is
MOSTLY, ALMOST_ALL = 0.5, 0.95
# A parent outline that its subdivisions cover to this share is dropped
TILED = 0.9
# A field inside another is a copy, not a field drawn inside a field, when this share of its
# outline runs along the other's outline (within TOUCH_DISTANCE m)
TOUCHING, TOUCH_DISTANCE = 0.25, 10


def _overlaps(geoms):
    """Every pair of overlapping geometries in both directions, with the overlap's area"""
    left, right = shapely.STRtree(geoms).query(geoms, predicate="intersects")
    pair = left < right
    left, right = left[pair], right[pair]
    area = shapely.area(shapely.intersection(geoms[left], geoms[right]))
    pair = area > 0
    left, right, area = left[pair], right[pair], area[pair]
    return (
        np.concatenate([left, right]),
        np.concatenate([right, left]),
        np.concatenate([area, area]),
    )


def find_overlaps(gdf):
    """Why each field goes so that a piece of land is annotated once: "region", "parent" or
    "copy", or "" to keep it.

    The source annotates some land twice: a region that annotated chips of another region again,
    parent outlines next to their subdivisions, copies of a field cut off at a chip edge and
    shifted copies. Fields drawn inside another field and real holes stay.
    """
    geoms = shapely.make_valid(gdf.geometry.to_crs(EQUAL_AREA_CRS).values)
    area = shapely.area(geoms)
    region = gdf["region"].to_numpy()
    rank = np.array([RANK.get(r, 1) for r in region])
    # the row number in the region's file decides between copies, whatever the input order
    row = gdf["id"].str.rsplit("-", n=1).str[1].astype(int).to_numpy()
    left, right, overlap = _overlaps(geoms)
    order = np.lexsort((row[right], region[right], row[left], region[left]))
    left, right, overlap = left[order], right[order], overlap[order]
    left_in = overlap / area[left]  # the share of left that lies inside right
    right_in = overlap / area[right]
    same = region[left] == region[right]
    reason = np.full(len(gdf), "", dtype=object)

    def kept(fields):
        return reason[fields] == ""

    def share_under(field, pairs):
        others = right[pairs & (left == field)]
        others = others[kept(others)]
        if len(others) == 0:
            return 0.0
        under = shapely.intersection(geoms[field], shapely.union_all(geoms[others]))
        return shapely.area(under) / area[field]

    # (a) a field of a region with a higher rank goes if half of it lies under the other
    # region's fields or if it holds half of one of them
    yields = ~same & (rank[left] > rank[right])
    fields = np.unique(left[yields])
    for field in fields[np.argsort(rank[fields], kind="stable")]:
        held = right[yields & (left == field) & (right_in >= MOSTLY)]
        if kept(held).any() or share_under(field, yields) >= MOSTLY:
            reason[field] = "region"

    # (b) a parent outline that two or more subdivisions (smaller fields mostly inside it)
    # cover; the largest first, so that a grandparent goes before its children are judged
    children = same & (area[right] < area[left]) & (right_in >= MOSTLY)
    parents = np.unique(left[children])
    for field in parents[np.lexsort((row[parents], region[parents], -area[parents]))]:
        if kept(field) and kept(right[children & (left == field)]).sum() >= 2:
            if share_under(field, children) >= TILED:
                reason[field] = "parent"

    # (c) a copy: a field almost all inside another that touches its outline or covers most of
    # it goes; of two fields that each lie mostly inside the other, the later in the file goes
    for i in np.flatnonzero(same & (left_in >= MOSTLY)):
        a, b = left[i], right[i]
        if not (kept(a) and kept(b)):
            continue
        a_inside, b_inside = left_in[i] >= ALMOST_ALL, right_in[i] >= ALMOST_ALL
        if a_inside and not b_inside:
            outline = shapely.boundary(geoms[a])
            along = shapely.intersection(
                outline, shapely.buffer(shapely.boundary(geoms[b]), TOUCH_DISTANCE)
            )
            if right_in[i] >= MOSTLY or shapely.length(along) >= TOUCHING * shapely.length(outline):
                reason[a] = "copy"
        elif a_inside or (not b_inside and right_in[i] >= MOSTLY):
            reason[a if row[a] > row[b] else b] = "copy"
    return reason


class Converter(FiboaBaseConverter):
    sources = {
        f"{BUCKET}/{region}/{region}Annotations_{year}.gpkg": f"{region}Annotations_{year}.gpkg"
        for region, (year, _) in REGIONS.items()
    }

    id = "wri_trazo"
    # the files are in several CRS (Web Mercator, UTM, lon/lat)
    crs = "EPSG:4326"
    short_name = "Trazo"
    title = "Trazo field boundary annotations for South America"
    description = """
Agricultural field boundaries drawn by hand by World Resources Institute (WRI) and Arizona State
University annotators (in Paraguay with Mundo Agropecuario) in 25 sampling regions across South
America, 2020-2024, to adapt the
Fields of The World (FTW) field boundary models to South American agriculture. The regions are
ecoregions (Chaco, Chiquitania, Araucaria, Amazon, Cerrado, Caatinga, Pampas and others) where the
baseline model performed poorly, about 500 samples in Paraguay from Mundo Agropecuario's data,
Mato Grosso samples chosen by active learning, and three randomly sampled test regions.

Each region was annotated for one year, which is each field's determination date (1 January of
that year). The three test regions (`testchiquitania`, `testmatogrosso`, `testsoy`) were sampled
randomly, the statistically rigorous choice for evaluation; the others were chosen for poor model
performance, a query strategy or partner data (WRI's own chip files split those about 90/10 into
train and val). `wri_trazo_ml` adds a `split`: `test` for the three test regions, `train` for the
others. `basemap` is the imagery the annotators drew on: monthly Planet basemaps or, in three
regions, Sentinel-2 alone.

Land that the source annotates twice is kept once. Some Mato Grosso regions annotated the same
chips: a few train fields that lie under `testmatogrosso` fields and
`matogrosso_brazil_lowconfidences` fields that lie under `matogrosso_brazil_confidences` fields
are dropped. Within a region, a parent outline that its subdivisions cover is dropped for them,
and so are copies of a field: polygons held twice, copies cut off at a chip edge and redrawn
or shifted copies. Fields drawn inside another field without a hole in it are kept.

Every field inside the 256x256 Sentinel-2 chips of WRI's training data is annotated; annotations
that reach beyond a chip are kept, but land outside the chips is not completely labelled.

Grupp et al. (2026): Field Boundaries of South America. World Resources Institute & Arizona State
University, https://www.wri.org/research/field-boundaries-south-america
    """
    provider = (
        "World Resources Institute and Arizona State University "
        "<https://source.coop/wri-data-lab/trazoannotations>"
    )
    attribution = (
        "Grupp et al. (2026), Field Boundaries of South America, "
        "World Resources Institute & Arizona State University"
    )
    license = "CC-BY-4.0"

    columns = {
        "id": "id",
        "geometry": "geometry",
        "determination:datetime": "determination:datetime",
        "region": "region",
        "basemap": "basemap",
    }
    column_additions = {"determination:method": "manual"}
    missing_schemas = {
        "properties": {
            "region": {
                "type": "string",
                "enum": sorted(REGIONS),
                "description": "The Trazo sampling region (a folder of the source data)",
            },
            "basemap": {
                "type": "string",
                "enum": ["planet", "sentinel-2"],
                "description": "The imagery the annotators drew on",
            },
        }
    }

    def file_migration(self, gdf, path, uri, layer=None):
        match = FILE_NAME.match(os.path.basename(path))
        if not match or match["region"] not in REGIONS:
            raise ValueError(f"Not a Trazo annotation file: {path}")
        region, year = match["region"], int(match["year"])
        if "year" in gdf.columns and set(gdf["year"].dropna().astype(int)) - {year}:
            raise ValueError(f"{path}: the year column disagrees with the file name ({year})")
        if gdf.crs is None:
            # lowmonte and peruvianamazon declare no CRS; their coordinates are lon/lat
            minx, miny, maxx, maxy = gdf.total_bounds
            if not (-180 <= minx <= maxx <= 180 and -90 <= miny <= maxy <= 90):
                raise ValueError(f"{path} has no CRS and its coordinates are not lon/lat")
            gdf = gdf.set_crs("EPSG:4326")
        # The source has no identifier; the row number in the region's file is stable
        gdf["id"] = [f"{region}-{i}" for i in range(len(gdf))]
        # Some files hold the same polygon twice (683 pairs in matogrosso_brazil_lcdib); keep the
        # first, so a field is counted once and the ids stay the source row numbers
        gdf = gdf[~gdf.geometry.to_wkb().duplicated()].copy()
        gdf["region"] = region
        gdf["determination:datetime"] = pd.Timestamp(f"{year}-01-01", tz="UTC")
        return super().file_migration(gdf, path, uri, layer)

    def migrate(self, gdf):
        gdf["basemap"] = gdf["region"].map(lambda r: REGIONS[r][1])
        reason = find_overlaps(gdf)
        dropped = reason != ""
        if dropped.any():
            counts = pd.Series(reason[dropped]).value_counts().sort_index().to_dict()
            self.info(f"Dropping fields that annotate land again: {counts}")
            gdf = gdf[~dropped]
        return super().migrate(gdf)
