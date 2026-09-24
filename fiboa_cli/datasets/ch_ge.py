from .ch_base import CHBaseConverter

# One layer with every year since 2017, rebuilt weekly from the previous Friday's database state
ZIP = "https://ge.ch/sitg/geodata/SITG/OPENDATA/AGR_SURFACE_AGRICOLE_RECENSEE-SHP.zip"


class Converter(CHBaseConverter):
    id = "ch_ge"
    canton = "GE"
    variants = {
        str(year): {ZIP: "AGR_SURFACE_AGRICOLE_RECENSEE-SHP.zip"} for year in range(2026, 2016, -1)
    }
    short_name = "Switzerland, Geneva"
    title = "Field boundaries for the canton of Geneva, Switzerland"
    description = """
The agricultural parcels that Geneva's farmers georeference every year for the direct payments
("surfaces agricoles recensées"), from the canton's geoportal SITG, which publishes every year
since 2017 in one layer. The usage is named in French; the code is the federal one. The current
year is provisional until December.
    """
    provider = (
        "État de Genève, Office cantonal de l'agriculture et de la nature <https://ge.ch/sitg/>"
    )
    license = "opendata.swiss terms: Open use. Must provide the source; SITG conditions d'utilisation, level A <https://sitg.ge.ch/ressources/conditions-utilisation-donnees>"
    attribution = "Données SITG, État de Genève — Surfaces agricoles recensées, https://ge.ch/sitg/geodata/SITG/OPENDATA/AGR_SURFACE_AGRICOLE_RECENSEE-SHP.zip"

    def select_variant(self, variant):
        super().select_variant(variant)
        year = int(self.variant)
        # one file holds every year; a few rows carry no code and would fail the required crop:code
        self.column_filters["bezugsjahr"] = lambda col: col == year
        self.column_filters["lnf_code"] = lambda col: col.notna()

    def file_migration(self, gdf, path, uri, layer=None):
        gdf = gdf.rename(
            columns={
                "ID": "nutzungsidentifikator",
                "CODE_FED": "lnf_code",
                "TYPE": "nutzung",
                "SHAPE_AREA": "flaeche_m2",
                "EXERCICE": "bezugsjahr",
            }
        )
        # both come as float because of a few nulls; the string cast of the base follows
        gdf["lnf_code"] = gdf["lnf_code"].astype("Int64")
        gdf["bezugsjahr"] = gdf["bezugsjahr"].astype("Int64")
        gdf["kanton"] = self.canton
        gdf["ist_ueberlagernd"] = False  # the layer carries no overlapping elements
        return gdf
