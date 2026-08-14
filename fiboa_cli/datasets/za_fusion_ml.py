from .za_fusion import ZaFusionConverter
from .commons.ml_splits import MlSplitsMixin


class ZaFusionMlConverter(MlSplitsMixin, ZaFusionConverter):

    def file_migration(self, gdf, path, uri, layer=None):
        gdf["split"] = "train" if "train" in path else "test"
        return super().file_migration(gdf, path, uri, layer)

    def migrate(self, gdf):
        gdf["id"] = gdf["split"] + "_" + gdf["fid"].astype(str)
        return super().migrate(gdf)
