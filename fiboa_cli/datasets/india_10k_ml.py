from os.path import dirname, join

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from .india_10k import IndiaConverter
from .commons.ml_splits import MlSplitsMixin


class India10kMlConverter(MlSplitsMixin, IndiaConverter):

    def migrate(self, gdf):
        # Load splits CSV and keep only train/val/test entries
        csv_path = join(dirname(__file__), "data-files", "india_splits_grid20x20_v2.csv")
        splits_df = pd.read_csv(csv_path)
        splits_df = splits_df[splits_df["fold"].isin(["train", "val", "test"])]

        # Convert CSV lat/lon into a GeoDataFrame of points
        splits_gdf = gpd.GeoDataFrame(
            splits_df,
            geometry=[Point(lon, lat) for lat, lon in zip(splits_df["lat"], splits_df["lon"])],
            crs="EPSG:4326",
        )

        # Ensure matching CRS
        if gdf.crs != splits_gdf.crs:
            gdf = gdf.to_crs("EPSG:4326")

        # Match each field to the nearest split point by centroid
        centroids = gdf.copy()
        centroids["_orig_idx"] = range(len(centroids))
        centroids.geometry = centroids.geometry.centroid

        joined = centroids.sjoin_nearest(
            splits_gdf[["geometry", "fold"]],
            how="left",
            distance_col="dist",
        )

        # Keep only the closest match per field
        joined = joined.sort_values("dist").drop_duplicates(subset="_orig_idx", keep="first")
        joined = joined.sort_values("_orig_idx")

        # Assign splits
        gdf["split"] = joined["fold"].values

        return super().migrate(gdf)

