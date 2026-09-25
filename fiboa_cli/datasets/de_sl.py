from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.converter_wfs import WFSConverterMixin
from ..conversion.fiboa_converter import FiboaBaseConverter

BASE_URL = (
    "https://geoportal.saarland.de/gdi-sl/inspirewfs_Existierende_Bodennutzung_Antragsschlaege"
)


class Converter(AdminConverterMixin, WFSConverterMixin, FiboaBaseConverter):
    id = "de_sl"
    admin_subdivision_code = "SL"
    short_name = "Germany, Saarland"
    title = "Field boundaries for Saarland, Germany"
    description = """This dataset contains data transformed into the INSPIRE data model “Land Use” of the IACS areas applied for within the framework of agricultural land promotion (GIS application) from the Saarland."""
    provider = "Ministerium für Umwelt, Klima, Mobilität, Agrar und Verbraucherschutz <https://geoportal.saarland.de>"
    attribution = "©GDI-SL 2024"
    license = "cc-by-4.0"
    extensions = {"https://fiboa.org/flik-extension/v0.2.0/schema.yaml"}

    wfs_url = BASE_URL
    wfs_params = {
        "typeNames": "elu:ExistingLandUseObject",
        # The media type contains a ";", which has to be percent-encoded. Passed through raw,
        # the server reads the parameter as "application/gml+xml" and rejects it.
        "outputFormat": "application/gml+xml; version=3.2",
    }
    # The WFS accepts larger pages, but 2500 keeps each response around 8 MB.
    wfs_page_size = 2500

    # The service publishes no area attribute, so metrics:area is measured from the geometry.

    columns = {
        "geometry": "geometry",
        "identifier": "id",
        "flik": "flik",  # derived in migrate(); NOT the id, one field block can hold several parcels
        "name": "name",
    }
    missing_schemas = {"properties": {"name": {"type": "string"}}}

    def migrate(self, gdf):
        # The FLIK is the first 16 characters of the last underscore-separated segment of the
        # identifier, e.g. …_DESLLI00002529002224568 -> DESLLI0000252900. The remaining seven
        # digits number the application parcel within the field block.
        gdf["flik"] = gdf["identifier"].str.rsplit("_", n=1).str[-1].str[:16]
        return super().migrate(gdf)
