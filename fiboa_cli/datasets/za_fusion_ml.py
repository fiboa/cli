from .commons.ml_splits import MlSplitsMixin
from .za_fusion import ZaFusionConverter


class ZaFusionMlConverter(MlSplitsMixin, ZaFusionConverter):
    def file_migration(self, gdf, path, uri, layer=None):
        gdf["split"] = "train" if "train" in path else "test"
        return super().file_migration(gdf, path, uri, layer)

    # Build unique IDs from split + fid to avoid collisions between files
    id_columns = ("split", "fid")
    id_separator = "_"
