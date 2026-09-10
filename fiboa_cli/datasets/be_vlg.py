from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import AddHCATMixin

PREFIX = "https://www.landbouwvlaanderen.be/bestanden/gis/"


class Converter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    # Every archive holds exactly one GeoPackage, but its name is not the name of
    # the archive: 2020 ships "Landbouwgebruikspercelen2020_igb15-05_uitgebreid_
    # (toestand_19-03-2021).gpkg" inside "Landbouwgebruikspercelen_2020_uitgebreid_
    # toestand_19-03-2021_GPKG.zip". Glob for it instead of deriving it.
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

    # The 2020 GeoPackage holds a byte sequence no UTF-8 decoder accepts (0xEF at
    # position 6 of a value), so reading it the normal way dies before the first
    # row arrives; cp1252 reads it, and costs nothing because every other value
    # in the file is ASCII. The other campaigns decode as UTF-8, and forcing
    # cp1252 on them would silently mangle any accented crop name.
    CP1252_EDITIONS = {"2020"}

    def layer_filter(self, layer, uri):
        # The 2026 GeoPackage carries a QGIS "layer_styles" table beside the
        # parcels. Its single row was read as a field, kept an index of its own
        # and so repeated an id; it only stayed out of the published file
        # because the empty-geometry guard dropped it afterwards.
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

    def migrate(self, gdf):
        if "maincrop_code" in gdf.columns:
            gdf = gdf.rename(columns=self.RENAMES_2026)
            if "BT_OMSCH" not in gdf.columns:  # no farm-typology column any more
                gdf["BT_OMSCH"] = None
        return super().migrate(gdf)

    # REF_ID references the parcel, and a row is one crop declared on it, so it
    # repeats whenever a parcel carries more than one: 183 references cover 367
    # of the 515,747 rows of 2018, some with two different crops on the same
    # geometry (winter barley and winter wheat on 414623668, both 0.6238 ha),
    # some with the same crop twice. It is published as `block_id`, and the row
    # index does the identifying — safe here because an edition is one layer of
    # one file.
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
