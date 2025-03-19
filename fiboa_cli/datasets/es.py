from fiboa_cli.convert_utils import BaseConverter
from fiboa_cli.datasets.commons.data import read_data_csv


class ESBaseConverter(BaseConverter):
    """
    Base Converter for Spain
    Asssumes a source column with the SIGPAC-Land Use code
    The Land Use code is filtered for agricultural use and transformed into a high-level crop type

    "Cultivo Declarado" is what we would prefer, but the "Recinto" is the best to be found so far

    For Spanish Sources, see https://www.cartodruid.es/en/-/descargar-sigpac-comunidad-autonoma
    There seems to be a National Layer; https://inspire-geoportal.ec.europa.eu/srv/api/records/87ce5171-d713-4eec-a1f3-2b9dd94cad91
    """

    use_code_attribute = "uso_sigpac"

    extensions = {
        "https://fiboa.github.io/crop-extension/v0.1.0/schema.yaml",
        "https://fiboa.github.io/administrative-division-extension/v0.1.0/schema.yaml",
    }
    column_additions = {
        # https://www.euskadi.eus/contenidos/informacion/pac2015_pagosdirectos/es_def/adjuntos/Anexos_PAC_marzo2015.pdf
        # https://www.fega.gob.es/sites/default/files/files/document/AD-CIRCULAR_2-2021_EE98293_SIGC2021.PDF
        # Very generic list
        "admin:country_code": "ES",
        "crop:code_list": "https://fiboa.org/code/es/sigpac/land_use.csv",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        assert self.id.startswith("es_"), "Assuming Spanish subclass"

        def code_filter(col):
            return ~col.isin("AG/CA/ED/FO/IM/IS/IV/TH/ZC/ZU/ZV/MT".split("/") + [None])

        self.column_filters = {self.use_code_attribute: code_filter}
        self.column_additions["admin:subdivision_code"] = self.id[len("es_") :].upper()

    def migrate(self, gdf):
        # This actually is a land use code. Not sure if we should put this in crop:code
        rows = read_data_csv("es_coda_uso.csv")
        mapping = {row["original_code"]: row["original_name"] for row in rows}
        mapping_en = {row["original_code"]: row["name_en"] for row in rows}
        gdf["crop:name"] = gdf[self.use_code_attribute].map(mapping)
        gdf["crop:name_en"] = gdf[self.use_code_attribute].map(mapping_en)
        return gdf
