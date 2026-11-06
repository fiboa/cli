import pandas as pd
from vecorel_cli.vecorel.extensions import ADMIN_DIVISION

from ..conversion.fiboa_converter import FiboaBaseConverter

BUCKET = "https://africa-field-boundary-labels.s3.us-west-2.amazonaws.com"
FIELDS = "mapped_fields_final.parquet"
CATALOG = "label-catalog-filtered.csv"


class LacunaLabelsConverter(FiboaBaseConverter):
    sources = {f"{BUCKET}/{FIELDS}": FIELDS, f"{BUCKET}/{CATALOG}": CATALOG}
    id = "lacuna_labels"
    short_name = "Mapping Africa"
    title = "Mapping Africa: crop field boundary labels for Africa, 2017-2023"
    description = """
Crop field boundaries digitised by trained labellers over Planet NICFI monthly basemaps at
sites (0.005° cells, about 550 m) across 39 African countries, 2017-2023, from the
[Lacuna Fund](https://lacunafund.org/) project led by [Farmerline](https://farmerline.co/)
with [Spatial Collective](https://spatialcollective.com/) and the Agricultural Impacts
Research Group at Clark University ([lacunalabels](https://github.com/agroimpacts/lacunalabels)).

Only the assignments in the project's filtered label catalog are kept, which is one labelling
per site; sites labelled with no fields have no rows. Each field is dated by the month of the
basemap it was digitised on. `label_class` is the catalog's assignment class (1a, 1b, 1d:
expert-labelled quality-control sites; 2: one labeller; 4: one of three labellers), and
`qscore` / `rscore` are the labeller's quality scores against the expert labels: one value
per labeller, not per field.

The labels are not wall-to-wall: fields can be missing from a site, so unlabelled land is
unknown, not non-field.

Estes, L. D., Wussah, A., Asipunu, M., Gathigi, M., Kovačič, P., Muhando, J.,
Yeboah, B. V., Addai, F. K., Akakpo, E. S., Allotey, M. K., Amkoya, P., Amponsem, E.,
Donkoh, K. D., Ha, N., Heltzel, E., Juma, C., Mdawida, R., Miroyo, A., Mucha, J.,
Mugami, J., Mwawaza, F., Nyarko, D. A., Oduor, P., Ohemeng, K. N., Segbefia, S. I. D.,
Tumbula, T., Wambua, F., Xeflide, G. H., Ye, S., Yeboah, F.(2024). A region-wide,
multi-year set of crop field boundary labels for Africa. arXiv:2412.18483.

The labels are published at https://zenodo.org/records/11060871 and can be used in accordance
with [Planet's participant license agreement for the NICFI contract](https://go.planet.com/nicfi-pla-2024).
    """
    provider = (
        "Agricultural Impacts Research Group, Clark University "
        "<https://github.com/agroimpacts/lacunalabels>"
    )
    attribution = "Estes et al. (2024), Lacuna Fund; labels digitised over Planet NICFI basemaps"
    license = "Planet NICFI participant license agreement <https://go.planet.com/nicfi-pla-2024>"

    extensions = {ADMIN_DIVISION}
    columns = {
        "id": "id",
        "geometry": "geometry",
        "determination:datetime": "determination:datetime",
        "admin:country_code": "admin:country_code",
        "name": "site",
        "assignment_id": "assignment_id",
        "label_class": "label_class",
        "labeller": "labeller",
        "qscore": "qscore",
        "rscore": "rscore",
        "category": "label_category",
    }
    missing_schemas = {
        "properties": {
            "site": {"type": "string", "description": "The labelled site (a 0.005° cell)"},
            "assignment_id": {
                "type": "int64",
                "description": "The labelling task in the project's label catalog",
            },
            "label_class": {
                "type": "string",
                "enum": ["1a", "1b", "1d", "2", "4"],
                "description": "Assignment class: 1a/1b/1d expert, 2 one labeller, "
                "4 one of three labellers",
            },
            "labeller": {"type": "string", "description": "Anonymised labeller or expert team"},
            "qscore": {
                "type": "float",
                "description": "The labeller's mean quality score against expert labels "
                "(one value per labeller)",
            },
            "rscore": {
                "type": "float",
                "description": "The labeller's share of assignments rated acceptable "
                "(one value per labeller)",
            },
            "label_category": {
                "type": "string",
                "enum": [
                    "annualcropland",
                    "fallow",
                    "treecrop",
                    "unsure1",
                    "unsure2",
                    "cloudshadow",
                ],
                "description": "The class the labeller gave the polygon",
            },
        }
    }

    def read_data(self, paths, **kwargs):
        # The catalog CSV is a side table, not geodata: read it here, join it in migrate()
        catalog = [p for p in paths if p[0].endswith(".csv")]
        if len(catalog) != 1:
            raise ValueError(f"Expected one {CATALOG}, got {[p[0] for p in catalog]}")
        # keep_default_na=False: Namibia's site codes start with "NA"
        self.catalog = pd.read_csv(catalog[0][0], dtype=str, keep_default_na=False)
        return super().read_data([p for p in paths if not p[0].endswith(".csv")], **kwargs)

    def migrate(self, gdf):
        raw = self.catalog
        cat = pd.DataFrame(
            {
                "name": raw["name"],
                "assignment_id": raw["assignment_id"].astype("int64"),
                "label_class": raw["Class"],
                "labeller": raw["Labeller"],
                "qscore": pd.to_numeric(raw["Qscore"], errors="coerce"),
                "rscore": pd.to_numeric(raw["Rscore"], errors="coerce"),
                "month": raw["image"].str.extract(r"_(\d{4}-\d{2})\.tif$", expand=False),
            }
        )
        if cat["month"].isna().any():
            raise ValueError(f"{CATALOG} has rows without a YYYY-MM basemap month in `image`")
        gdf = gdf.copy()
        gdf["assignment_id"] = gdf["assignment_id"].astype("int64")
        # Inner join: only the catalog's assignments (one per site) are kept
        gdf = gdf.merge(cat, on=["name", "assignment_id"], how="inner")
        gdf["id"] = gdf["fid"].astype("int64").astype(str)
        gdf["determination:datetime"] = pd.to_datetime(gdf.pop("month") + "-01", utc=True)
        gdf["admin:country_code"] = gdf["name"].str[:2]
        return super().migrate(gdf)
