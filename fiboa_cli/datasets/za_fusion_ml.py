from .za_fusion import ZaFusionConverter
from .commons.ml_splits import MlSplitsMixin


class ZaFusionMlConverter(MlSplitsMixin, ZaFusionConverter):

    def file_migration(self, gdf, path, uri, layer=None):
        if "train" in path:
            gdf["_source_split"] = "train"
        else:
            gdf["_source_split"] = "test"
        return super().file_migration(gdf, path, uri, layer)

    def migrate(self, gdf):
        gdf["split"] = gdf["_source_split"].astype(object)
        gdf["id"] = gdf["_source_split"] + "_" + gdf["fid"].astype(str)
        return super().migrate(gdf)
