from .commons.ml_splits import MlSplitsMixin
from .wri_trazo import Converter as TrazoConverter


class Converter(MlSplitsMixin, TrazoConverter):
    def migrate(self, gdf):
        # the three randomly sampled test regions are the test split
        gdf["split"] = gdf["region"].str.startswith("test").map({True: "test", False: "train"})
        return super().migrate(gdf)
