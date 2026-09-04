import pandas as pd
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.converter_rest import EsriRESTConverterMixin
from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.de_iacs import DEIACSMixin

# Layer 0 is "LC.LandCoverSurfaces.Feldbloecke", layer 1 the landscape elements.
FIELD_BLOCK_LAYER = 0


class DESTConverter(AdminConverterMixin, DEIACSMixin, EsriRESTConverterMixin, FiboaBaseConverter):
    id = "de_st"
    admin_subdivision_code = "ST"
    short_name = "Germany, Saxony-Anhalt"
    title = "Field blocks for Saxony-Anhalt, Germany"
    description = """
The field blocks ("Feldblöcke") of Saxony-Anhalt, the reference parcels of its Land Parcel
Identification System (LPIS). The data is derived from the InVeKoS records and transformed into the
INSPIRE "Land Cover" data model, so each field block carries a land cover class from the national
IACS code list alongside its FLIK. The landscape elements ("Landschaftselemente"), which the same
service publishes as a second layer, are not included. No area is published, so it is computed from
the geometry.
"""

    provider = "Ministerium für Wirtschaft, Tourismus, Landwirtschaft und Forsten (MWL) Sachsen-Anhalt <https://mwl.sachsen-anhalt.de>"
    attribution = "© Ministerium für Wirtschaft, Tourismus, Landwirtschaft und Forsten des Landes Sachsen-Anhalt, dl-de/by-2-0"
    license = "DL-DE-BY-2.0"

    extensions = {"https://fiboa.org/flik-extension/v0.2.0/schema.yaml"}

    rest_base_url = "https://geodatenportal.sachsen-anhalt.de/arcgisinspire/rest/services/INSPIRE_MWL/DLM50_MWL_LC_INVEKOS/MapServer"

    # One variant per snapshot, mapped to the ID_VERSIONID that selects it, newest first.
    variants = {str(year): f"{year}.1" for year in range(2023, 2020, -1)}

    # SHAPE.AREA is in square degrees, so the area is derived from the geometry instead. The result
    # is in m² and must not be scaled.
    area_is_in_ha = False
    area_calculate_missing = True

    columns = {
        "geometry": "geometry",
        "flik": ("flik", "id"),  # derived in migrate(); unique, unlike in Baden-Württemberg
        "CLASS_CODE": "crop:code",  # already the bare de.iacs code
        "BEGINLIFESPANVERSION": "determination:datetime",
        "area": "metrics:area",  # not in the source; created by area_calculate_missing
    }
    column_migrations = {"BEGINLIFESPANVERSION": lambda col: pd.to_datetime(col, unit="ms")}

    def rest_layer_filter(self, layers):
        return next(layer for layer in layers if layer["id"] == FIELD_BLOCK_LAYER)

    def get_urls(self):
        if not self.variant:
            self.variant = next(iter(self.variants))

        # All three snapshots live in one table and share their ID_LOCALID, so without this filter
        # every field block is returned three times. The mixin reads rest_params in get_data().
        self.rest_params = {"where": f"ID_VERSIONID='{self.variants[self.variant]}'"}
        return super().get_urls()

    def migrate(self, gdf):
        # The FLIK is the second underscore-separated segment of the INSPIRE local identifier, e.g.
        # LCU_FB_DESTLI0509850059_955064 -> DESTLI0509850059
        gdf["flik"] = gdf["ID_LOCALID"].str.split("_").str[2]
        return super().migrate(gdf)
