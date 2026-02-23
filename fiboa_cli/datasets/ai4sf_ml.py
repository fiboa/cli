from .ai4sf import Ai4SfConverter
from .commons.ml_splits import MlSplitsMixin


class Ai4SfMlConverter(MlSplitsMixin, Ai4SfConverter):

    def migrate(self, gdf):
        # Download file with splits
        urls = {
            "https://phys-techsciences.datastations.nl/api/access/datafile/100418?gbrecs=true": "tiles_asia.gpkg",
        }
        paths = self.download_files(urls, self.cache)
        tiles = self.read_data(paths, **self.open_options)

        # Add splits
        splits = tiles[["id", "country", "split"]].drop_duplicates(subset=["id", "country"])
        gdf = gdf.merge(splits, on=["id", "country"], how="left")
        gdf["split"] = gdf["split"].replace({"validate": "val"})

        return super().migrate(gdf)
