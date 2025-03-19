from ..convert_utils import BaseConverter


class LacunaLabelsConverter(BaseConverter):
    sources = "https://zenodo.org/records/11060871/files/mapped_fields_final.parquet?download=1"
    id = "lacuna"
    short_name = "Lacuna Labels"
    title = "A region-wide, multi-year set of crop field boundary labels for Africa"
    description = """
    The [Lacunalabels](https://github.com/agroimpacts/lacunalabels/) repository hosts
    the analytical code and pointers to datasets
    resulting from a project to generate a continent-wide set of crop field
    labels for Africa covering the years 2017-2023. The data are intended
    for training and assessing machine learning models that can be used to
    map agricultural fields over large areas and multiple years.

    The project was funded by the [Lacuna Fund](https://lacunafund.org/),
    and led by [Farmerline](https://farmerline.co/), in collaboration with
    [Spatial Collective](https://spatialcollective.com/) and the
    [Agricultural Impacts Research Group](agroimpacts.info) at
    [Clark University](https://www.clarku.edu/departments/geography/).

    Please refer to the [technical report](docs/report/technical-report.pdf)
    for more details on the methods used to develop the dataset, an analysis
    of label quality, and usage guidelines.

    Data is published at https://zenodo.org/records/11060871 and can be used in accordance with
    [Planet’s participant license agreement for the NICFI contract](https://go.planet.com/nicfi-pla-2024).
    """
    providers = [
        {
            "name": "Agricultural Impacts Research Group",
            "url": "https://github.com/agroimpacts/lacunalabels/",
            "roles": ["producer"],
        },
        {"name": "Planet Labs PBC", "url": "https://www.planet.com/", "roles": ["licensor"]},
    ]
    attribution = "Planet Labs Inc."

    license = {
        "title": "Planet NICFI participant license agreement",
        "href": "https://go.planet.com/nicfi-pla-2024",
        "type": "text/html",
        "rel": "license",
    }

    columns = {
        "geometry": "geometry",
        "id": "id",
        "category": "category",
    }

    missing_schemas = {
        "properties": {
            "category": {"type": "string"},
        }
    }
