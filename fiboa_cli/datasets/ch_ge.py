from .ch_base import CHBaseConverter

# every year since 2017 in one layer, rebuilt weekly
ZIP = "https://ge.ch/sitg/geodata/SITG/OPENDATA/AGR_SURFACE_AGRICOLE_RECENSEE-SHP.zip"


class Converter(CHBaseConverter):
    canton = "GE"
    variants = {
        str(year): {ZIP: "AGR_SURFACE_AGRICOLE_RECENSEE-SHP.zip"} for year in range(2026, 2016, -1)
    }
    description = """
The agricultural parcels that Geneva's farmers georeference every year for the direct payments
("surfaces agricoles recensées"), from the canton's geoportal SITG, which publishes every year
since 2017 in one layer. The usage is named in French; the code is the federal one. The current
year is provisional until December.
    """
    provider = (
        "État de Genève, Office cantonal de l'agriculture et de la nature <https://ge.ch/sitg/>"
    )
    attribution = "Données SITG, État de Genève — Surfaces agricoles recensées, https://ge.ch/sitg/geodata/SITG/OPENDATA/AGR_SURFACE_AGRICOLE_RECENSEE-SHP.zip"
    source_columns = {
        "ID": "nutzungsidentifikator",
        "CODE_FED": "lnf_code",
        "TYPE": "nutzung",
        "SHAPE_AREA": "flaeche_m2",
        "EXERCICE": "bezugsjahr",
    }

    def select_variant(self, variant):
        super().select_variant(variant)
        year = int(self.variant)
        self.column_filters["bezugsjahr"] = lambda col: col == year  # one file holds every year
