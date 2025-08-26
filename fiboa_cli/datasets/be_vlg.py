from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import ec_url

PREFIX = "https://www.landbouwvlaanderen.be/bestanden/gis/"


class Converter(AdminConverterMixin, FiboaBaseConverter):
    variants = {
        k: {PREFIX + v: [v.replace("_GPKG.zip", ".gpkg")]}
        for k, v in (
            (2024, "Landbouwgebruikspercelen_2024_-_Voorlopig_(extractie_15-10-2024)_GPKG.zip"),
            (2023, "Landbouwgebruikspercelen_2023_-_Definitief_(extractie_28-03-2024)_GPKG.zip"),
            (2022, "Landbouwgebruikspercelen_2022_-_Definitief_(extractie_26-06-2023)_GPKG.zip"),
            (2021, "Landbouwgebruikspercelen_2021_-_Definitief_(extractie_15-03-2022)_GPKG.zip"),
            (2020, "Landbouwgebruikspercelen_2020_uitgebreid_toestand_19-03-2021_GPKG.zip"),
            (2019, "Landbouwgebruikspercelen_2019_-_Definitief_(extractie_20-03-2020)_GPKG.zip"),
            (2018, "Landbouwgebruikspercelen_2018_-_Definitief_(extractie_23-03-2022)_GPKG.zip"),
        )
    }
    id = "be_vlg"
    short_name = "Belgium, Flanders"
    admin_subdivision_code = "VLG"
    title = "Field boundaries for Flanders, Belgium"
    description = """
    Since 2020, the Department of Agriculture and Fisheries has been publishing a more extensive set of data related to agricultural use plots (from the 2008 campaign).
    From 2023, the downloadable dataset of agricultural use plots will also include the specialization given by the company (= company typology) and that is given to the plots of the company. Based on the typology, the companies are divided into 4 major specializations: arable farming, horticulture, livestock farming and mixed farms. The specialization of each company is calculated annually according to a European method and is based on the standard output of the various agricultural productions on the company. It is therefore an economic specialization and not a reflection of all agricultural production on the company.
    """

    providers = [
        {
            "name": "Agentschap Landbouw & Zeevisserij (Government)",
            "url": "https://landbouwcijfers.vlaanderen.be/open-geodata-landbouwgebruikspercelen",
            "roles": ["producer", "licensor"],
        }
    ]

    attribution = "Bron: Dept. LV"
    license = {
        "title": "Licentie modellicentie-gratis-hergebruik/v1.0",
        "href": "https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0",
        "type": "text/html",
        "rel": "license",
    }

    columns = {
        "geometry": "geometry",
        "BT_BRON": "source",
        "BT_OMSCH": "typology",
        "GRAF_OPP": "metrics:area",
        "REF_ID": "id",
        "GWSCOD_H": "crop:code",
        "GWSNAM_H": "crop:name",
    }
    extensions = {"https://fiboa.github.io/crop-extension/v0.2.0/schema.yaml"}
    column_additions = {
        "determination:datetime": "2024-03-28T00:00:00Z",
        "crop:code_list": ec_url("be_vlg_2021.csv"),
    }

    missing_schemas = {"properties": {"source": {"type": "string"}, "typology": {"type": "string"}}}
