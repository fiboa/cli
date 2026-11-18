from .ai4sf import Ai4SfConverter
from .commons.ml_splits import MlSplitsMixin

SPLITS = "tiles_asia.gpkg"


class Ai4SfMlConverter(MlSplitsMixin, Ai4SfConverter):
    sources = {
        **Ai4SfConverter.sources,
        "https://phys-techsciences.datastations.nl/api/access/datafile/100418?gbrecs=true": SPLITS,
    }
    side_files = (SPLITS,)

    def migrate(self, gdf):
        tiles = self.read_side_file(SPLITS)
        splits = tiles[["id", "country", "split"]].drop_duplicates(subset=["id", "country"])
        gdf = gdf.merge(splits, on=["id", "country"], how="left")
        gdf["split"] = gdf["split"].replace({"validate": "val"})
        return super().migrate(gdf)
