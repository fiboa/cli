from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import AddHCATMixin

PREFIX = "https://www.landbouwvlaanderen.be/bestanden/gis/"


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    # Each archive holds one GeoPackage, but not under the name of the zip
    # (2020 least of all), so glob for it rather than deriving it.
    variants = {
        str(k): {PREFIX + v: ["*.gpkg"]}
        for k, v in (
            (2026, "agpa_2026_2026-06-02_public.zip"),
            (2025, "Landbouwgebruikspercelen_2025_-_Voorlopig_(extractie_02-06-2025)_GPKG.zip"),
            (2024, "Landbouwgebruikspercelen_2024_-_Definitief_(extractie_27-03-2025)_GPKG.zip"),
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

    provider = "Agentschap Landbouw & Zeevisserij (Government) <https://landbouwcijfers.vlaanderen.be/open-geodata-landbouwgebruikspercelen>"

    attribution = "Bron: Dept. LV"
    license = "Licentie modellicentie-gratis-hergebruik/v1.0 <https://data.vlaanderen.be/id/licentie/modellicentie-gratis-hergebruik/v1.0>"

    # The 2020 GeoPackage holds a byte no UTF-8 decoder accepts, and everything
    # else in it is ASCII. Only that campaign: forcing cp1252 on the others
    # would mangle an accented crop name instead of failing.
    CP1252_EDITIONS = {"2020"}

    def layer_filter(self, layer, uri):
        # The 2026 GeoPackage carries a QGIS "layer_styles" table whose single
        # row was read as a field.
        return layer != "layer_styles"

    def read_data(self, paths, **kwargs):
        if self.variant in self.CP1252_EDITIONS:
            kwargs["encoding"] = "cp1252"
        return super().read_data(paths, **kwargs)

    # the 2026 "agpa" edition renamed every column to English
    RENAMES_2026 = {
        "reference_id": "REF_ID",
        "maincrop_code": "GWSCOD_H",
        "maincrop_title": "GWSNAM_H",
        "area_ha": "GRAF_OPP",
    }

    # Flanders publishes in Lambert 72; the 2020 snapshot leaves its SRS
    # undefined while holding those metres, which put 258615.94 into the STAC
    # extent as an east longitude.
    LAMBERT_72 = "EPSG:31370"

    def migrate(self, gdf):
        if gdf.crs is None or gdf.crs.to_epsg() is None:
            gdf = gdf.set_crs(self.LAMBERT_72, allow_override=True)
        if "maincrop_code" in gdf.columns:
            gdf = gdf.rename(columns=self.RENAMES_2026)
            if "BT_OMSCH" not in gdf.columns:  # no farm-typology column any more
                gdf["BT_OMSCH"] = None
        return super().migrate(gdf)

    # REF_ID references the parcel and a row is one crop declared on it, so it
    # repeats: 183 references cover 367 of the 515,747 rows of 2018. It is
    # published as block_id; the row index identifies the field, which is safe
    # because an edition is one layer of one file.
    index_as_id = True
    columns = {
        "geometry": "geometry",
        "id": "id",
        "BT_OMSCH": "typology",
        "GRAF_OPP": "metrics:area",
        "REF_ID": "block_id",
        "GWSCOD_H": "crop:code",
        "GWSNAM_H": "crop:name",
    }
    # Each edition is the campaign year of its variant; the old constant
    # "2024-03-28" was the extraction date of one edition applied to all of them.
    use_variant_as_determination = True
    ec_mapping_csv = "be_vlg_2021.csv"

    missing_schemas = {
        "properties": {
            "typology": {"type": "string"},
            "block_id": {"type": "string"},
        }
    }
