import geopandas as gpd
from shapely.geometry import box
from .commons.ml_splits import MlSplitsMixin
from .rw_rwanda import RwRwandaConverter

# Pre-computed WGS84 bounding boxes of all 57 Rwanda train tiles.
# Extracted once from https://data.source.coop/nasa/rwanda-field-boundary-competition/labels/train/
# Eliminates runtime rasterio/HTTP dependency.
TRAIN_TILE_BOUNDS_WGS84 = [
    (30.313811, -1.523916, 30.324798, -1.512933),  # tile 00
    (30.368657, -1.490882, 30.379643, -1.479900),  # tile 01
    (30.390544, -1.546095, 30.401530, -1.535113),  # tile 02
    (30.302997, -1.402548, 30.313983, -1.391565),  # tile 03
    (30.357671, -1.524002, 30.368657, -1.513019),  # tile 04
    (30.335655, -1.579128, 30.346642, -1.568145),  # tile 05
    (30.291882, -1.523916, 30.302868, -1.512933),  # tile 06
    (30.302825, -1.546009, 30.313811, -1.535027),  # tile 07
    (30.357714, -1.501908, 30.368700, -1.490925),  # tile 08
    (30.313768, -1.557035, 30.324755, -1.546052),  # tile 09
    (30.335741, -1.512933, 30.346727, -1.501951),  # tile 10
    (30.401487, -1.557163, 30.412474, -1.546181),  # tile 11
    (30.368614, -1.546095, 30.379601, -1.535113),  # tile 12
    (30.346727, -1.501908, 30.357714, -1.490925),  # tile 13
    (30.335741, -1.534984, 30.346727, -1.524002),  # tile 14
    (30.313811, -1.534984, 30.324798, -1.524002),  # tile 15
    (30.412517, -1.501994, 30.423503, -1.491011),  # tile 16
    (30.324841, -1.457720, 30.335827, -1.446737),  # tile 17
    (30.357714, -1.479857, 30.368700, -1.468874),  # tile 18
    (30.324798, -1.490840, 30.335784, -1.479857),  # tile 19
    (30.368657, -1.512976, 30.379643, -1.501994),  # tile 20
    (30.346684, -1.546052, 30.357671, -1.535070),  # tile 21
    (30.368743, -1.413660, 30.379729, -1.402677),  # tile 22
    (30.302739, -1.590153, 30.313725, -1.579171),  # tile 23
    (30.412431, -1.590281, 30.423417, -1.579299),  # tile 24
    (30.324755, -1.546009, 30.335741, -1.535027),  # tile 25
    (30.368700, -1.457806, 30.379686, -1.446823),  # tile 26
    (30.346727, -1.512933, 30.357714, -1.501951),  # tile 27
    (30.313811, -1.512890, 30.324798, -1.501908),  # tile 28
    (30.324841, -1.468788, 30.335827, -1.457806),  # tile 29
    (30.335655, -1.590196, 30.346642, -1.579213),  # tile 30
    (30.390501, -1.568188, 30.401487, -1.557206),  # tile 31
    (30.390673, -1.424686, 30.401659, -1.413703),  # tile 32
    (30.379601, -1.524002, 30.390587, -1.513019),  # tile 33
    (30.302911, -1.468746, 30.313897, -1.457763),  # tile 34
    (30.368786, -1.402591, 30.379772, -1.391608),  # tile 35
    (30.368700, -1.468831, 30.379686, -1.457849),  # tile 36
    (30.401616, -1.446780, 30.412602, -1.435797),  # tile 37
    (30.302825, -1.534941, 30.313811, -1.523959),  # tile 38
    (30.357757, -1.435711, 30.368743, -1.424728),  # tile 39
    (30.302825, -1.523916, 30.313811, -1.512933),  # tile 40
    (30.335784, -1.490840, 30.346770, -1.479857),  # tile 41
    (30.335784, -1.468788, 30.346770, -1.457806),  # tile 42
    (30.313811, -1.501865, 30.324798, -1.490882),  # tile 43
    (30.302868, -1.501865, 30.313854, -1.490882),  # tile 44
    (30.313768, -1.546009, 30.324755, -1.535027),  # tile 45
    (30.291882, -1.512890, 30.302868, -1.501908),  # tile 46
    (30.412560, -1.490925, 30.423546, -1.479943),  # tile 47
    (30.368743, -1.435711, 30.379729, -1.424728),  # tile 48
    (30.335870, -1.424643, 30.346856, -1.413660),  # tile 49
    (30.324798, -1.501865, 30.335784, -1.490882),  # tile 50
    (30.390501, -1.579213, 30.401487, -1.568231),  # tile 51
    (30.357757, -1.446737, 30.368743, -1.435754),  # tile 52
    (30.357671, -1.535027, 30.368657, -1.524045),  # tile 53
    (30.401616, -1.468874, 30.412602, -1.457891),  # tile 54
    (30.368614, -1.524002, 30.379601, -1.513019),  # tile 55
    (30.401530, -1.524045, 30.412517, -1.513062),  # tile 56
]


def _get_train_tiles():
    """Return GeoDataFrame of train tile bounding boxes in WGS84.
    Uses pre-computed bounds - no rasterio or network calls needed."""
    geometries = [box(w, s, e, n) for w, s, e, n in TRAIN_TILE_BOUNDS_WGS84]
    return gpd.GeoDataFrame({"geometry": geometries}, crs="EPSG:4326")


class RwRwandaMlConverter(MlSplitsMixin, RwRwandaConverter):
    def file_migration(self, gdf, path, uri, layer=None):
        """Assign train/test split to each field via spatial join with
        train tile bounding boxes. No val split for Rwanda."""
        train_tiles = _get_train_tiles()
        gdf = gdf.reset_index(drop=True)
        joined = gpd.sjoin(
            gdf,
            train_tiles[["geometry"]],
            how="left",
            predicate="intersects",
        )
        # Drop duplicate rows created when a field overlaps multiple tiles
        joined = joined[~joined.index.duplicated(keep="first")]
        gdf["_source_split"] = (
            joined["index_right"].notna().map({True: "train", False: "test"})
        )
        return super().file_migration(gdf, path, uri, layer)

    def migrate(self, gdf):
        gdf["split"] = gdf["_source_split"].astype(object)
        return super().migrate(gdf)