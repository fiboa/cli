import pandas as pd
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.convert_gml import gml_assure_columns
from ..conversion.converter_wfs import WFSConverterMixin
from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.de_iacs import DEIACSMixin

BASE_URL = "https://gdiserv.bayern.de/srv66381/services/invekos_lpis-wfs"


class DEBYBlockConverter(AdminConverterMixin, DEIACSMixin, WFSConverterMixin, FiboaBaseConverter):
    id = "de_by_block"
    admin_subdivision_code = "BY"
    short_name = "Germany, Bavaria (blocks)"
    title = "Field blocks for Bavaria, Germany"
    description = """
This dataset contains the field blocks ("Feldstücke") of Bavaria, the reference parcels of its Land
Parcel Identification System (LPIS). A Feldstück is a contiguous agricultural area belonging to a
single farm operator; areas separated by roads, tracks or watercourses are not combined, and
differing tenure, use or fertiliser planning do not split one. Delineation follows the area eligible
for support, which comprises agricultural area, agriculturally usable area and eligible landscape
elements. The data is published in the "IACS in INSPIRE" (TG2) data model and republished twice a
year for the application procedure.
"""

    provider = "Bayerisches Staatsministerium für Ernährung, Landwirtschaft, Forsten und Tourismus <https://www.stmelf.bayern.de>"
    attribution = "© Bayerisches Staatsministerium für Ernährung, Landwirtschaft, Forsten und Tourismus, CC BY 4.0"
    license = "CC-BY-4.0"

    extensions = {"https://fiboa.org/flik-extension/v0.2.0/schema.yaml"}

    wfs_url = BASE_URL
    wfs_params = {
        "typeNames": "lpis:AgriculturalArea",
        # Without a sort the server pages in an unstable order: pages overlap and others are skipped.
        "sortBy": "lpis:id",
    }
    # Server-enforced maximum. Larger values are silently capped, so paging must use this number.
    wfs_page_size = 10_000

    # The service publishes no area attribute, so metrics:area is measured from the geometry.

    columns = {
        "geometry": "geometry",
        "flik": ("flik", "id"),  # derived in migrate(); unique, unlike in Baden-Württemberg
        "agricultural_area_type": "crop:code",  # added in file_migration()
        "validFrom": "determination:datetime",
    }
    column_migrations = {
        "validFrom": lambda col: pd.to_datetime(col),
        # …/codelist/de.iacs/AgriculturalAreaTypeValue/AL -> AL
        "agricultural_area_type": lambda col: col.str.rsplit("/", n=1).str[-1],
    }

    def file_migration(self, gdf, path, uri, layer=None):
        # The land cover class is carried as an xlink attribute, which the GML driver does not
        # guess into its generated schema, so ask for it explicitly. The href points into the
        # national de.iacs codelist; the xlink:title next to it only repeats the English label,
        # which the shared code list already supplies.
        return gml_assure_columns(
            gdf,
            path,
            uri,
            layer,
            agricultural_area_type={
                "ElementPath": "agriculturalAreaType@href",
                "Type": "String",
                "Width": 255,
            },
        )

    def migrate(self, gdf):
        # The FLIK is the last dot-separated segment of the identifier URI, e.g.
        # https://registry.gdi-de.org/id/de.by.inspire.invekos.lpis.aa.DEBYLI9412000570
        gdf["flik"] = gdf["id"].str.rsplit(".", n=1).str[-1]
        return super().migrate(gdf)
