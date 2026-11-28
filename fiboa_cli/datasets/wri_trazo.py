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

# Of the two active learning samples (low model confidence on farmland, and anywhere), whose
# chips overlap in places and are drawn in about as much detail there, the first gives way to
# the second (swap them to flip)
GIVES_WAY = "matogrosso_brazil_lowconfidences"
OTHER_SAMPLE = "matogrosso_brazil_confidences"
# Where regions annotated the same chips, the fields of the region with the higher rank give way
# (the others have rank 1); no field of a test region gives way to a train region
RANK = {"testchiquitania": 0, "testmatogrosso": 0, "testsoy": 0, GIVES_WAY: 2}
# Shares of a field's area: "mostly" and "almost all" inside another field, and two fields that
# each lie this much inside the other are one field drawn twice
MOSTLY, ALMOST_ALL, TWICE = 0.5, 0.95, 0.9
# A parent outline that its subdivisions cover to this share is dropped for them; below it, the
# parent stays and its subdivisions go, except those whose outline runs along less than CLEAR of
# the parent's: those are fields drawn inside it
TILED, CLEAR = 0.9, 0.05
# A field inside another is a clipped copy, not a field drawn inside a field, when this share of
# its outline runs along the other's outline (within TOUCH_DISTANCE m) and the rest is made of
# straight lines (at least this share of it, as clipping makes)
TOUCHING, TOUCH_DISTANCE, STRAIGHT = 0.25, 10, 0.5


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


def _outline(geom):
    """The exterior rings of a (multi)polygon, without its holes"""
    rings = [shapely.get_exterior_ring(p) for p in shapely.get_parts(geom) if not p.is_empty]
    return shapely.multilinestrings(rings) if rings else shapely.MultiLineString()


def _touches(inner, outer, share=TOUCHING, straight=False):
    """Whether this share of the inner field's outline runs along the outer's, and (if straight)
    the rest of it is made of straight lines, as when a copy is clipped by a chip box"""
    outline = _outline(inner)
    near = shapely.buffer(_outline(outer), TOUCH_DISTANCE)
    if shapely.length(shapely.intersection(outline, near)) < share * shapely.length(outline):
        return False
    if not straight:
        return True
    own = shapely.line_merge(shapely.difference(outline, near))
    lines = [line for line in shapely.get_parts(own) if line.length > 2 * TOUCH_DISTANCE]
    total = sum(line.length for line in lines)
    # a straight line, or two meeting at a corner, keeps at most three points when simplified
    simple = sum(line.length for line in lines if len(line.simplify(TOUCH_DISTANCE).coords) <= 3)
    return total == 0 or simple >= STRAIGHT * total


def find_overlaps(gdf):
    """Why each field goes so that a piece of land is annotated once: "region", "twice",
    "parent", "subdivision" or "copy", or "" to keep it.

    The source annotates some land twice: a region that annotated chips of another region again,
    a field drawn twice, parent outlines next to their subdivisions and copies of a field clipped
    by a chip box. Fields drawn inside another field and real holes stay.
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

    # a field goes if half of it lies under fields of regions with a lower rank
    yields = ~same & (rank[left] > rank[right])
    fields = np.unique(left[yields])
    for field in fields[np.argsort(rank[fields], kind="stable")]:
        if share_under(field, yields) >= MOSTLY:
            reason[field] = "region"

    # of a field drawn twice, the later row goes
    for i in np.flatnonzero(
        same & (left_in >= TWICE) & (right_in >= TWICE) & (row[left] > row[right])
    ):
        if kept(left[i]) and kept(right[i]):
            reason[left[i]] = "twice"

    # a parent outline with two or more subdivisions (smaller fields mostly inside it) goes if
    # they cover it, otherwise its subdivisions go; the largest first, so that a grandparent is
    # judged before its children
    children = same & (area[right] < area[left]) & (right_in >= MOSTLY)
    parents = np.unique(left[children])
    for field in parents[np.lexsort((row[parents], region[parents], -area[parents]))]:
        pieces = right[children & (left == field)]
        pieces = pieces[kept(pieces)]
        if not kept(field) or len(pieces) < 2:
            continue
        if share_under(field, children) >= TILED:
            reason[field] = "parent"
        else:
            for piece in pieces:
                if _touches(geoms[piece], geoms[field], share=CLEAR):
                    reason[piece] = "subdivision"

    # a field almost all inside another goes if it covers most of it or is a clipped copy;
    # of two fields that each lie mostly inside the other, the later row goes
    for i in np.flatnonzero(same & (left_in >= MOSTLY)):
        a, b = left[i], right[i]
        if not (kept(a) and kept(b)):
            continue
        if left_in[i] >= ALMOST_ALL and right_in[i] < ALMOST_ALL:
            if right_in[i] >= MOSTLY or _touches(geoms[a], geoms[b], straight=True):
                reason[a] = "copy"
        elif right_in[i] >= MOSTLY and right_in[i] < ALMOST_ALL:
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
    description = f"""
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
chips: train fields that lie mostly under `testmatogrosso` fields and `{GIVES_WAY}` fields
that lie mostly under `{OTHER_SAMPLE}` fields are dropped. Within a region, of a field
drawn twice the later one is dropped; a parent outline is dropped where its subdivisions cover
it, and otherwise the subdivisions that run along its outline; and so are copies of a field
clipped by a chip box (lying inside another field, partly along its outline, cut by straight
lines). Other fields drawn inside a field without a hole for them are kept.

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
