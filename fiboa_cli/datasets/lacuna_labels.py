from ..conversion.fiboa_converter import FiboaBaseConverter


class LacunaLabelsConverter(FiboaBaseConverter):
    sources = "https://africa-field-boundary-labels.s3.us-west-2.amazonaws.com/mapped_fields_final.parquet"
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
    of label quality, and usage guidelines, and the publication:

    Estes, L. D., Wussah, A., Asipunu, M., Gathigi, M., Kovačič, P., Muhando, J.,
    Yeboah, B. V., Addai, F. K., Akakpo, E. S., Allotey, M. K., Amkoya, P., Amponsem, E.,
    Donkoh, K. D., Ha, N., Heltzel, E., Juma, C., Mdawida, R., Miroyo, A., Mucha, J.,
    Mugami, J., Mwawaza, F., Nyarko, D. A., Oduor, P., Ohemeng, K. N., Segbefia, S. I. D.,
    Tumbula, T., Wambua, F., Xeflide, G. H., Ye, S., Yeboah, F.(2024). A region-wide,
    multi-year set of crop field boundary labels for Africa. arXiv:2412.18483.

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
        "id": "id",
        "name": "name",
        "assignment_id": "assignment_id",
        "image_date": "image_date",
        "completion_time": "completion_time",
        "category": "category",
        "geometry": "geometry",
    }

    missing_schemas = {
        "properties": {
            "name": {"type": "string"},
            "category": {"type": "string", "enum": ["annualcropland"]},
            "assignment_id": {"type": "string"},
            "image_date": {"type": "string"},
            "completion_time": {"type": "date-time"},
        }
    }
