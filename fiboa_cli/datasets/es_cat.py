import pandas as pd

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.data import read_data_csv


class ESCatConverter(FiboaBaseConverter):
    # Catalonia has its own coding list, not sublass of ESBaseConverter
    variants = {
        "2024": {
            "https://analisi.transparenciacatalunya.cat/api/views/yh94-j2n9/files/d90f5fca-ddd8-405d-a0d5-90609985e98e?download=true&filename=Cultius_DUN2024_SHP.zip": [
                "Cultius_DUN2024_GPKG/CULTIUS_DUN2024.gpkg"
            ]
        },
        "2023": {
            "https://analisi.transparenciacatalunya.cat/api/views/yh94-j2n9/files/b4299961-52ee-4fa0-a276-4594c8c094bc?download=true&filename=Cultius_DUN2023_GPKG.zip": [
                "Cultius_DUN2023_GPKG/CULTIUS_DUN2023.gpkg"
            ]
        },
        "2022": {
            "https://analisi.transparenciacatalunya.cat/api/views/yh94-j2n9/files/f1c8c463-ef4a-4821-8516-ff1884c0386a?download=true&filename=Cultius_DUN2022_SHP.zip": "Cultius_DUN2022.zip"
        },
        "2021": {
            "https://analisi.transparenciacatalunya.cat/api/views/yh94-j2n9/files/aef79c3c-c663-46ed-a535-ceb03a64b46b?download=true&filename=Cultius_DUN2021_SHP.zip": "Cultius_DUN2021.zip"
        },
        "2020": {
            "https://analisi.transparenciacatalunya.cat/api/views/yh94-j2n9/files/b47b0ab9-8324-40c7-b553-1015793a38a4?download=true&filename=Cultius_DUN2020_SHP.zip": "Cultius_DUN2020.zip"
        },
        "2019": {
            "https://analisi.transparenciacatalunya.cat/api/views/yh94-j2n9/files/58d46b1e-522f-428e-b089-aa8e4668fae9?download=true&filename=Cultius_DUN2019.zip": "Cultius_DUN2019.zip"
        },
        # More data at https://agricultura.gencat.cat/ca/ambits/desenvolupament-rural/sigpac/mapa-cultius/
    }
    id = "es_cat"
    short_name = "Catalonia"
    title = "Catalonia Crop Fields (Mapa de cultius)"
    description = """
        The Department of Agriculture, Livestock, Fisheries and Food makes available to the public the data from the crop map of Catalonia.
        This map allows you to locate the crops declared in the Agrarian Declaration - DUN submitted to the DACC.
    """
    providers = [
        {
            "name": "Catalonia Department of Agriculture, Livestock, Fisheries and Food",
            "url": "https://agricultura.gencat.cat/ca/ambits/desenvolupament-rural/sigpac/mapa-cultius/",
            "roles": ["producer", "licensor"],
        }
    ]
    attribution = "Catalonia Department of Agriculture, Livestock, Fisheries and Food"
    license = {
        "title": "The Open Information Use License - Catalonia",
        "href": "https://administraciodigital.gencat.cat/ca/dades/dades-obertes/informacio-practica/llicencies/",
        "type": "text/html",
        "rel": "license",
    }
    extensions = {"https://fiboa.github.io/crop-extension/v0.2.0/schema.yaml"}
    column_additions = {
        "crop:code_list": "https://fiboa.org/code/es/cat/crop.csv",
    }
    columns = {
        "geometry": "geometry",
        "id": "id",
        "campanya": "determination:datetime",
        "ha": "metrics:area",
        "cultiu": "crop:name",
        "crop:code": "crop:code",
        "crop:name_en": "crop:name_en",
    }
    open_options = dict(encoding="utf-8")
    column_migrations = {
        "campanya": lambda col: pd.to_datetime(col, format="%Y"),
    }

    index_as_id = True

    def layer_filter(self, layer, uri):
        return "cultius" in layer.lower()

    def migrate(self, gdf):
        # In 2023 gpkg, names are lowercase. But in 2022 shapefile, case is mixed
        to_lower = {k: k.lower() for k in gdf.columns if k != k.lower}
        if to_lower:
            gdf.rename(columns=to_lower, inplace=True)

        rows = read_data_csv("es_cat.csv")
        mapping = {row["original_name"]: row["original_code"] for row in rows}
        mapping_en = {row["original_name"]: row["translated_name"] for row in rows}
        missing = {k for k in gdf["cultiu"].unique() if k not in mapping}
        assert len(missing) == 0, f"Can not map crops {missing}"
        gdf["crop:code"] = gdf["cultiu"].map(mapping)
        gdf["crop:name_en"] = gdf["cultiu"].map(mapping_en)
        return gdf
