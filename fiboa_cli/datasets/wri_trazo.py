import os
import re

import pandas as pd

from ..conversion.fiboa_converter import FiboaBaseConverter

BUCKET = "https://data.source.coop/wri-data-lab/trazoannotations"

# Folder -> (year in the file name, basemap the annotators drew on), from each folder's
# "annotation info.txt": "Planet Labs Trainable: No" means a Sentinel-2 basemap
REGIONS = {
    "acre": (2020, "planet"),
    "altoparana": (2020, "planet"),
    "araucaria": (2023, "planet"),
    "caatinga": (2021, "planet"),
    "cerrado": (2021, "planet"),
    "chaco": (2020, "planet"),
    "chiquitania": (2020, "sentinel-2"),
    "humidchaco": (2022, "planet"),
    "lowmonte": (2023, "planet"),
    "maparaguay": (2024, "planet"),
    "matogrosso": (2020, "sentinel-2"),
    "matogrosso_brazil_confidences": (2020, "planet"),
    "matogrosso_brazil_lcdi": (2020, "planet"),
    "matogrosso_brazil_lcdib": (2020, "planet"),
    "matogrosso_brazil_lowconfidences": (2020, "planet"),
    "pampas": (2021, "planet"),
    "pantanal": (2023, "planet"),
    "para": (2020, "sentinel-2"),
    "peruvianamazon": (2022, "planet"),
    "rondonia": (2022, "planet"),
    "testchiquitania": (2020, "planet"),
    "testmatogrosso": (2020, "planet"),
    "testsoy": (2020, "planet"),
    "tocantins": (2024, "planet"),
    "uruguayansavannah": (2020, "planet"),
}
FILE_NAME = re.compile(r"^(?P<region>.+)Annotations_(?P<year>\d{4})\.gpkg$")


class Converter(FiboaBaseConverter):
    sources = {
        f"{BUCKET}/{region}/{region}Annotations_{year}.gpkg": f"{region}Annotations_{year}.gpkg"
        for region, (year, _) in REGIONS.items()
    }

    id = "wri_trazo"
    short_name = "Trazo"
    title = "Trazo field boundary annotations for South America"
    description = """
Agricultural field boundaries drawn by hand by World Resources Institute (WRI) and Arizona State
University annotators (in Paraguay with Mundo Agropecuario) in 25 sampling regions across South
America, 2020-2024, to adapt the
Fields of The World (FTW) field boundary models to South American agriculture. The regions are
ecoregions (Chaco, Chiquitania, Araucaria, Amazon, Cerrado, Caatinga, Pampas and others) where the
baseline model performed poorly, about 500 samples in Paraguay from Mundo Agropecuario's data,
Mato Grosso samples chosen by active learning, and three randomly sampled test regions.

Each region was annotated for one year, which is each field's determination date (1 January of
that year). `split` is `test` for the three randomly sampled test regions (`testchiquitania`,
`testmatogrosso`, `testsoy`), the statistically rigorous choice for evaluation, and `train` for
the others, which were chosen for poor model performance, a query strategy or partner data
(WRI's own chip files split those about 90/10 into train and val). Some Mato Grosso regions
overlap: a few `testmatogrosso` fields are also labelled in train regions, and many
`matogrosso_brazil_lowconfidences` fields are also in `matogrosso_brazil_confidences`.
`basemap` is the imagery the annotators drew on: monthly Planet basemaps or, in three regions,
Sentinel-2 alone. Polygons that a source file holds twice are kept once.

Every field inside the 256x256 Sentinel-2 chips of WRI's training data is annotated; annotations
that reach beyond a chip are kept, but land outside the chips is not completely labelled.

Grupp et al. (2026): Field Boundaries of South America. World Resources Institute & Arizona State
University, https://www.wri.org/research/field-boundaries-south-america
    """
    provider = (
        "World Resources Institute and Arizona State University "
        "<https://source.coop/wri-data-lab/trazoannotations>"
    )
    attribution = (
        "Grupp et al. (2026), Field Boundaries of South America, "
        "World Resources Institute & Arizona State University"
    )
    license = "CC-BY-4.0"

    columns = {
        "id": "id",
        "geometry": "geometry",
        "determination:datetime": "determination:datetime",
        "region": "region",
        "split": "split",
        "basemap": "basemap",
    }
    column_additions = {"determination:method": "manual"}
    missing_schemas = {
        "properties": {
            "region": {
                "type": "string",
                "enum": sorted(REGIONS),
                "description": "The Trazo sampling region (a folder of the source data)",
            },
            "split": {
                "type": "string",
                "enum": ["train", "test"],
                "description": "test for the randomly sampled test regions, train otherwise",
            },
            "basemap": {
                "type": "string",
                "enum": ["planet", "sentinel-2"],
                "description": "The imagery the annotators drew on",
            },
        }
    }

    def file_migration(self, gdf, path, uri, layer=None):
        match = FILE_NAME.match(os.path.basename(path))
        if not match or match["region"] not in REGIONS:
            raise ValueError(f"Not a Trazo annotation file: {path}")
        region, year = match["region"], int(match["year"])
        if "year" in gdf.columns and set(gdf["year"].dropna().astype(int)) - {year}:
            raise ValueError(f"{path}: the year column disagrees with the file name ({year})")
        if gdf.crs is None:
            # lowmonte and peruvianamazon declare no CRS; their coordinates are lon/lat
            minx, miny, maxx, maxy = gdf.total_bounds
            if not (-180 <= minx <= maxx <= 180 and -90 <= miny <= maxy <= 90):
                raise ValueError(f"{path} has no CRS and its coordinates are not lon/lat")
            gdf = gdf.set_crs("EPSG:4326")
        # The files are in several CRS (Web Mercator, UTM, lon/lat); they are concatenated
        gdf = gdf.to_crs("EPSG:4326")
        # The source has no identifier; the row number in the region's file is stable
        gdf["id"] = [f"{region}-{i}" for i in range(len(gdf))]
        # Some files hold the same polygon twice (683 pairs in matogrosso_brazil_lcdib); keep the
        # first, so a field is counted once and the ids stay the source row numbers
        gdf = gdf[~gdf.geometry.to_wkb().duplicated()].copy()
        gdf["region"] = region
        gdf["determination:datetime"] = pd.Timestamp(f"{year}-01-01", tz="UTC")
        return super().file_migration(gdf, path, uri, layer)

    def migrate(self, gdf):
        gdf["basemap"] = gdf["region"].map(lambda r: REGIONS[r][1])
        gdf["split"] = gdf["region"].str.startswith("test").map({True: "test", False: "train"})
        return super().migrate(gdf)
