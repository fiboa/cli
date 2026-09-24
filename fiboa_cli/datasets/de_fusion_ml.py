from .de_fusion import DeFusionConverter
from .commons.ml_splits import MlSplitsMixin


class DeFusionMlConverter(MlSplitsMixin, DeFusionConverter):

    def file_migration(self, gdf, path, uri, layer=None):
        # Train file contains "2018", test file contains "2019".
        gdf["split"] = "train" if "2018" in path else "test"
        return super().file_migration(gdf, path, uri, layer)

    # Build unique IDs from split + fid to avoid collisions between files
    id_columns = ("split", "fid")
    id_separator = "_"
