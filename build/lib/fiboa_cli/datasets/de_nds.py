import pandas as pd
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    """
    https://sla.niedersachsen.de/agrarfoerderung/schlaginfo/ (see download)
    The zip contains:
      - Schlaege = UD_25_S.shp
      - TeilLandschaftElemente = UD_25_TLE.shp
      - TeilSchlaege = UD_25_TS.shp
    """

    variants = {
        f"{year}": {
            f"https://sla.niedersachsen.de/mapbender_sla/download/schlaege_aktuell_{year}.zip": [
                f"UD_{year % 100}_S.shp"
            ]
        }
        for year in range(2025, 2020, -1)
    }
    id = "de_nds"
    admin_subdivision_code = "NI"
    short_name = "Germany, Lower Saxony/Bremen/Hamburg"
    title = "Crop Fields for Lower Saxony / Bremen / Hamburg, Germany"
    description = """A Crop Field (German: "Schlaege") is a contiguous agricultural area surrounded by permanent boundaries, which is cultivated with a single crop."""
    provider = "ML/SLA Niedersachsen <https://sla.niedersachsen.de/landentwicklung/LEA/>"
    attribution = "© ML/SLA Niedersachsen (2024), DL-DE-BY-2.0 (www.govdata.de/DL-DE-BY-2.0), Daten bearbeitet"
    license = "DL-DE-BY-2.0"
    extensions = {"https://fiboa.org/flik-extension/v0.2.0/schema.yaml"}

    # https://www.sla.niedersachsen.de/download/141235/Verzeichnis_Nutzungscodes.xlsx
    ec_mapping_csv = "de.csv"
    columns = {
        "geometry": "geometry",
        "FLIK": "flik",
        "SCHLAGNR": "subfield_id",
        "NC_FESTG": "crop:code",
        "ANTRAGSJAH": "determination:datetime",
        "AKTUELLEFL": "metrics:area",
    }
    missing_schemas = {
        "properties": {
            "subfield_id": {"type": "int64"},
        }
    }
    column_migrations = {"ANTRAGSJAH": lambda col: pd.to_datetime(col, format="%Y")}

    def migrate(self, gdf):
        if "NC_FESTG" not in gdf.columns:
            code = {"KULTURARTF", "KULTURCODE", "KC_FESTG"} & set(gdf.columns)
            del self.columns["NC_FESTG"]
            self.columns[code.pop()] = "crop:code"

        if "AKTUELLEFL" not in gdf.columns:
            del self.columns["AKTUELLEFL"]
            self.columns["AKT_FL"] = "metrics:area"

        return super().migrate(gdf)
