from .de_fusion import DeFusionConverter
from .commons.ml_splits import MlSplitsMixin


class DeFusionMlConverter(MlSplitsMixin, DeFusionConverter):

    def file_migration(self, gdf, path, uri, layer=None):
        # Tag rows with the correct split based on which file they came from.
        # The train file contains "2018" and the test file contains "2019".
        if "2018" in path:
            gdf["_source_split"] = "train"
        else:
            gdf["_source_split"] = "test"
        return super().file_migration(gdf, path, uri, layer)

    def migrate(self, gdf):
        # Assign split from temp marker
        gdf["split"] = gdf["_source_split"].astype(object)

        # Build unique IDs from split + fid before dropping the temp marker.
        # Using split as prefix avoids collisions between train/test files
        # since both files contain overlapping fid values.
        gdf["id"] = gdf["_source_split"] + "_" + gdf["fid"].astype(str)

        gdf = gdf.drop(columns=["_source_split"])
        return super().migrate(gdf)
