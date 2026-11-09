import pandas as pd
from vecorel_cli.vecorel.extensions import ADMIN_DIVISION

from ..conversion.fiboa_converter import FiboaBaseConverter

BUCKET = "https://africa-field-boundary-labels.s3.us-west-2.amazonaws.com"
FIELDS = "mapped_fields_final.parquet"
CATALOG = "label-catalog-filtered.csv"
# The month of the Planet NICFI basemap a site was labelled on, from the catalog's `image`
MONTH = r"_(\d{4}-\d{2})\.tif$"


class LacunaLabelsConverter(FiboaBaseConverter):
    sources = {f"{BUCKET}/{FIELDS}": FIELDS, f"{BUCKET}/{CATALOG}": CATALOG}
    side_files = (CATALOG,)
    id = "lacuna"
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
    id_columns = ("fid",)
    columns = {
        "geometry": "geometry",
        "image": "determination:datetime",
        "admin:country_code": "admin:country_code",
        "name": "site",
        "assignment_id": "assignment_id",
        "Class": "label_class",
        "Labeller": "labeller",
        "Qscore": "qscore",
        "Rscore": "rscore",
        "category": "label_category",
        "completion_time": "completion_time",
    }
    column_migrations = {
        "image": lambda col: pd.to_datetime(col.str.extract(MONTH, expand=False) + "-01", utc=True),
        "Qscore": lambda col: pd.to_numeric(col, errors="coerce"),
        "Rscore": lambda col: pd.to_numeric(col, errors="coerce"),
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
            "completion_time": {
                "type": "date-time",
                "description": "When the labeller finished the assignment",
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

    def migrate(self, gdf):
        # keep_default_na=False: Namibia's site codes start with "NA"
        catalog = self.read_side_file(CATALOG, dtype=str, keep_default_na=False)
        catalog = catalog[
            ["name", "assignment_id", "Class", "Labeller", "Qscore", "Rscore", "image"]
        ]
        if catalog["image"].str.extract(MONTH, expand=False).isna().any():
            raise ValueError(f"{CATALOG} has rows without a YYYY-MM basemap month in `image`")
        catalog["assignment_id"] = catalog["assignment_id"].astype("int64")
        gdf["assignment_id"] = gdf["assignment_id"].astype("int64")
        # Inner join: only the catalog's assignments (one per site) are kept; a catalog row
        # listed twice fails instead of duplicating the fields
        gdf = gdf.merge(catalog, on=["name", "assignment_id"], how="inner", validate="many_to_one")
        gdf["admin:country_code"] = gdf["name"].str[:2]
        return super().migrate(gdf)
