import os
import re
import unicodedata

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin, load_ec_mapping

# Up to 2023 the country is split into "Culturas_<district>" layers, from 2025 into
# "T<NUTS 3 code>" layers. Both files carry other layers too (parcel blocks, land cover,
# an empty "Culturas" container, a non-spatial "Codes" table) that are not field boundaries.
DATA_LAYER = re.compile(r"^(Culturas_.+|T[0-9A-Z]{3})$")

# 2020-2022 are shaped differently again: one archive per campaign holding the sub-parcel
# geometry as several regional files, named differently every year. They need their own
# patterns, and 2021 needs DATA_LAYER *not* to apply: its archive also holds
# "Culturas_2021", a 3.4M-row attribute table with no geometry at all, which
# "Culturas_.+" would otherwise select and convert as if it were field boundaries.
EDITION_LAYER = {
    "2022": re.compile(r"^Ocupacoes_solo"),
    "2021": re.compile(r"^Ocupacoes_solo_"),
    "2020": re.compile(r"^Subparcelas"),
}

# The archive members to read. Region names are not spelled consistently -- 2020 has both
# "SubparcelasNORTE" and "Subparcelas_ALENTEJO" -- and several carry accents that survive
# extraction differently depending on the tool, so those are globbed; get_data resolves
# each entry to exactly one file and fails loudly if it matches none or several.
MEMBERS = {
    "2022": [
        "Continente.gpkg",
        "Madeira.gpkg",
        "Ca_22_Acores_Ocidental.gpkg",
        "Ca_22_Acores_Oriental_Central.gpkg",
    ],
    "2021": [
        "Ocupacoes_solo_ALENTEJO.shp",
        "Ocupacoes_solo_ALGARVE.shp",
        "Ocupacoes_solo_AREA_METROPOLITANA_DE_LISBOA.shp",
        "Ocupacoes_solo_Centro.shp",
        "Ocupacoes_solo_Norte.shp",
        "Ocupacoes_solo__acores_central_oriental.shp",
        "Ocupacoes_solo__acores_ocidental.shp",
        "Ocupacoes_solo_madeira.shp",
    ],
    # Norte_N is listed before Norte_S so the duplicated ids are dropped from Norte_S,
    # keeping the Norte_N copy; OVERLAPPING_MEMBERS names that pair explicitly.
    "2019": [
        "Ocupacoes_solo_AML.shp",
        "Ocupacoes_solo_Alentejo.shp",
        "Ocupacoes_solo_Algarve.shp",
        "Ocupacoes_solo_Centro_N.shp",
        "Ocupacoes_solo_Centro_S.shp",
        "Ocupacoes_solo_Norte_S.shp",
        "Ocupacoes_solo_RAA.shp",
        "Ocupacoes_solo_RAM.shp",
        "ocupacoes_solo_n_1.shp",
        "ocupacoes_solo_n_2.shp",
    ],
    "2018": [
        "Ocupacoes_solo_AML.shp",
        "Ocupacoes_solo_Alentejo.shp",
        "Ocupacoes_solo_Algarve.shp",
        "Ocupacoes_solo_Centro_N.shp",
        "Ocupacoes_solo_Centro_S.shp",
        "Ocupacoes_solo_Norte_N.shp",
        "Ocupacoes_solo_Norte_S.shp",
        "Ocupacoes_solo_RAA.shp",
        "Ocupacoes_solo_RAM.shp",
        "ocupacoes.solo.Norte_N1.2018jun10.shp",
    ],
    "2017": [
        "Ocupacoes_solo_AML.shp",
        "Ocupacoes_solo_Alentejo.shp",
        "Ocupacoes_solo_Algarve.shp",
        "Ocupacoes_solo_Centro_N.shp",
        "Ocupacoes_solo_Centro_S.shp",
        "Ocupacoes_solo_Norte_S.shp",
        "Ocupacoes_solo_RAA.shp",
        "Ocupacoes_solo_RAM.shp",
        "ocupacoes_solo_norte_n1.shp",
        "ocupacoes_solo_norte_n2.shp",
    ],
    "2020": [
        "Subparcelas_ALENTEJO.shp",
        "SubparcelasALGARVE.shp",
        "SubparcelasCENTRO.shp",
        "SubparcelasNORTE.shp",
        "Subparcelas_A*ores_Central_Oriental.shp",
        "Subparcelas_A*ores_Ocidental.shp",
        "Subparcelas_Madeira.shp",
        "Subparcelas*REA_METROPOLITANA_DE_LISBOA.shp",
    ],
}

# 2017-2019 come from the same "2017-2020/" archive family as 2020 but are shaped
# differently again: ten regional shapefiles per campaign, each its own single layer, so
# layer_filter has nothing to choose between and selection happens entirely in MEMBERS.
# Beside them sit "Parcelas_<region>" (the parcel blocks, PAR_NUM only) which are not
# field boundaries, plus junk that is simply never named here: 2019 ships seven
# "*.shp.EPC0444.340.5752.sr.lock" files and an orphan "osas_az_ocidental.qpj".
#
# The northern block is packaged differently every year and is the only part published in
# ETRS89 / Portugal TM06 rather than WGS 84; note the dots inside 2018's filename.
NAME_EDITIONS = ("2019", "2018", "2017")

# 2018 ships the north twice. Ocupacoes_solo_Norte_N and Ocupacoes_solo_Norte_S share
# 154,980 OSA_IDs, and those rows are exact duplicates: same PAR_NUM, same crop, geometry
# equal to 1e-9, zero area difference. Norte_S is not wholly contained in Norte_N though
# -- 386,611 of its 541,591 rows are unique -- so the member cannot simply be dropped and
# the collision is resolved row by row, keeping the Norte_N copy. Every other member of
# every edition is disjoint, so overlap anywhere else is a defect and raises. Keyed on the
# layer name, which for a shapefile is the basename without its extension.
OVERLAPPING_MEMBERS = {"2018": {"Ocupacoes_solo_Norte_S": "Ocupacoes_solo_Norte_N"}}

# 2017's two island files publish no OSA_ID at all -- only PAR_NUM, a land cover class and
# an area -- so there is no identifier to carry. PAR_NUM is not unique within either file
# (131,760 rows over 111,430 values in RAA, 45,854 over 33,245 in RAM; up to 24 rows share
# one value), so the id is the row's position under an explicit stable sort on
# (PAR_NUM, representative point x, representative point y). That is a total order except
# for rows identical on all three, whose relative order the stable sort takes from the
# shapefile's own record sequence, which is fixed. The base is four orders of magnitude
# above the largest OSA_ID ever published (41,356,676, in 2019), so a synthesised id can
# never be confused with or collide with a real one.
ISLAND_ID_BASE = 10**12

# 2018 lost the accented character from some crop names, leaving a literal "?" in its
# place: "FEIJ?O" for "FEIJÃO". Resolved once, offline, by treating "?" as exactly one
# character and matching the result against the normalised pt.csv original_name column;
# every one of the fourteen matched exactly one entry, so the resolution is mechanical
# rather than a judgement about what the name means. Kept as a fixed table rather than a
# runtime wildcard, and _crop_codes raises on any "?" name that is not in it, so a future
# ambiguous one fails loudly instead of going null. 2017 and 2019 contain no "?" at all.
QUESTION_MARK_ALIASES = {
    "AGRI?O": "AGRIAO",
    "AVEL?": "AVELA",
    "CONSOCIAC?ES ANUAIS E OUTRAS CULT FORRAG ANUAIS": (
        "CONSOCIACOES ANUAIS E OUTRAS CULT FORRAG ANUAIS"
    ),
    "EP BOSQUETE E FORMAC?ES RELIQUIAIS AREA UTIL": (
        "EP BOSQUETE E FORMACOES RELIQUIAIS AREA UTIL"
    ),
    "FEIJ?O": "FEIJAO",
    "GR?O DE BICO": "GRAO DE BICO",
    "LIM?O": "LIMAO",
    "MAC?": "MACA",
    "MACICOS OU FORMAC?ES RELIQUIAIS OU NOTAVEIS": ("MACICOS OU FORMACOES RELIQUIAIS OU NOTAVEIS"),
    "MEL?O": "MELAO",
    "PINH?O": "PINHAO",
    "ROM?": "ROMA",
    "SOBREIRO PARA PRODUC?O DE CORTICA": "SOBREIRO PARA PRODUCAO DE CORTICA",
    "SUPERFICIE ARBUSTIVA N?O PASTOREAVEL": "SUPERFICIE ARBUSTIVA NAO PASTOREAVEL",
}

# A crop column, whatever the edition spells it. The count varies per file rather than per
# year -- 2017 runs to c12 and 2019's Azores file to C28 -- the case is mixed inside a
# single year, and the range is not contiguous: 2018's Norte_N1 has c1..c7 and c9, no c8.
# Only the first is carried, as in 2020-2022, but it is found by number rather than by
# assuming it is spelled "C1".
CROP_COLUMN = re.compile(r"^[Cc](\d{1,2})$")


def normalise_crop_name(value, keep_question_mark=False):
    """Fold a published crop name to its comparison key.

    2017 spells the same crop four ways in one campaign -- PASTAGENS_ARBUSTIVAS and
    PASTAGENS ARBUSTIVAS, PRADOS_TEMPORARIOS and PRADOS TEMPORÁRIOS -- so separators and
    accents have to go before anything matches. Values are uppercase in all three years;
    upper() is belt and braces. Underscores need no special case: they are outside the
    allowed set below and become spaces with every other separator.
    """
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.upper()
    allowed = "A-Z0-9 ?" if keep_question_mark else "A-Z0-9 "
    text = re.sub(f"[^{allowed}]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


# 2020 and 2021 keep the crop code in a geometry-less DBF beside the regional geometry,
# keyed on the land-occupation id. 2021 spells both the file and the key differently,
# and types the key as a float.
CROP_TABLE = {"2021": "Culturas_2021.dbf", "2020": "culturas_2020.dbf"}

# Source columns worth carrying past the per-file step. The regional files hold up to
# twelve crop columns plus land-cover descriptions; dropping them before the regions are
# concatenated keeps ~5M rows of unused strings out of memory.
KEEP = (
    "geometry",
    "OSA_ID",
    "PAR_ID",
    "CUL_ID",
    "CUL_CODIGO",
    "PAR_NUM",
    "C1",
    "CT_português",
    "Shape_Area",
    "Shape_Length",
)


class PTConverter(AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    id = "pt"
    title = "Field boundaries for Portugal"
    short_name = "Portugal"
    description = "Open field boundaries (identificação de parcelas) from Portugal"
    # see https://www.ifap.pt/isip/ows/
    BASE = "https://www.ifap.pt/isip/ows/resources/"
    variants = {
        "2025": BASE + "2025/culturas.gpkg",
        "2023": BASE + "2023/Continente.gpkg",
        # 2020-2022 ship an archive of regional files; naming the members makes the base
        # converter extract it and hand each one to file_migration separately.
        "2022": {BASE + "2022/2022.zip": MEMBERS["2022"]},
        "2021": {BASE + "2021/2021.zip": MEMBERS["2021"]},
        "2020": {BASE + "2017-2020/2020.zip": MEMBERS["2020"]},
        "2019": {BASE + "2017-2020/2019.zip": MEMBERS["2019"]},
        "2018": {BASE + "2017-2020/2018.zip": MEMBERS["2018"]},
        "2017": {BASE + "2017-2020/2017.zip": MEMBERS["2017"]},
        "2016": BASE + "2011_2016/2016.zip",
        "2015": BASE + "2011_2016/2015.zip",
        # ...
    }

    def layer_filter(self, layer, uri):
        # 2017-2019 are shapefiles, one layer each, named after the file. There is nothing
        # to choose between, and the layer name is the region ("Ocupacoes_solo_AML"), which
        # no pattern here matches -- so filtering by name would reject every file. What is
        # and is not a field boundary is decided by MEMBERS for these editions.
        if self.variant in NAME_EDITIONS:
            return True
        return bool(EDITION_LAYER.get(self.variant, DATA_LAYER).match(layer))

    provider = (
        "IPAP - Instituto de Financiamento da Agricultura e Pescas <https://www.ifap.pt/isip/ows/>"
    )
    license = "No conditions apply <https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply>"
    columns = {
        "geometry": "geometry",
        # CUL_ID identifies the crop parcel and is unique across every layer of
        # both editions (3,568,852 of 3,568,852 in 2025); OSA_ID is the land
        # occupation polygon it lies in, which several parcels can share.
        "CUL_ID": "id",
        "OSA_ID": "block_id",
        "CUL_CODIGO": "crop:code",
        # The crop name is only published up to 2023; from 2025 the code is all there is.
        "CT_português": "crop:name",
        "Shape_Area": "metrics:area",
        "Shape_Length": "metrics:perimeter",
    }
    extensions = {"https://fiboa.org/crop-extension/v0.2.0/schema.yaml"}
    ec_mapping_csv = "https://fiboa.org/code/pt/pt.csv"
    use_variant_as_determination = True
    area_is_in_ha = False
    missing_schemas = {
        "properties": {
            "block_id": {"type": "int64"},
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._crop_table = None
        self._regions = []
        self._name_to_code = None
        self._seen_ids = {}
        self._island_rows = 0
        # The largest OSA_ID the source has published so far, which is what the island id
        # range has to stay clear of. Kept apart from _seen_ids, because that also holds
        # the ids this converter mints and comparing against those would be circular.
        self._max_published_id = None
        self._unmapped_names = {}

    def _crop_name_lookup(self):
        """pt.csv original_name -> original_code, keyed on the normalised name.

        AddHCATMixin keys on original_code whenever the mapping CSV has that column, and
        pt.csv does, so a name-only edition cannot simply hand its name through as
        crop:name and expect HCAT to follow. The name has to become a code here, before
        post_migrate runs. self.ec_mapping is set at the same time so the mixin reuses
        this list rather than fetching the CSV a second time.
        """
        if self._name_to_code is not None:
            return self._name_to_code

        if self.ec_mapping is None:
            self.ec_mapping = load_ec_mapping(self.ec_mapping_csv, url=self.mapping_file)

        lookup = {}
        for entry in self.ec_mapping:
            key = normalise_crop_name(entry["original_name"])
            code = entry["original_code"]
            # Two names carry two codes each, and they are not the same case.
            #
            # POUSIO is 089 and 89: one code zero-padded two ways, identical in every
            # other column, so the choice really cannot change any output. min() takes
            # the zero-padded spelling, which is how every other code in the file is
            # written.
            #
            # AZEVEM is 067 and 076, and those are two rows with the same hcat:code
            # (3301090205) and hcat:name (lolium_ryegrass) but different translated_name:
            # "ryegrass" for 067, "lolium" for 076. translated_name becomes hcat:name_en,
            # so the pick is visible in the output on 35,597 rows across 2017-2019. It is
            # a choice between two valid English renderings of one crop, not a distinction
            # that matters, and dropping the name for being ambiguous would cost those
            # rows their crop code for nothing. 067 is pinned deliberately: "ryegrass" is
            # the common name, where "lolium" is the genus.
            if key == "AZEVEM":
                lookup[key] = "067"
                continue
            if key not in lookup or code < lookup[key]:
                lookup[key] = code

        self._name_to_code = lookup
        return lookup

    def _crop_codes(self, names):
        """Resolve published crop names to pt.csv codes, raising on an unresolved '?'."""
        lookup = self._crop_name_lookup()
        # na_action keeps a missing crop missing: without it NaN normalises to the string
        # "NAN" and is reported as an unmapped crop name.
        keys = names.map(
            lambda v: normalise_crop_name(v, keep_question_mark=True), na_action="ignore"
        )
        # The alias table is consulted first and only for names that still hold a "?", so
        # an entry can never shadow a name the source spells correctly.
        resolved = keys.map(
            lambda k: QUESTION_MARK_ALIASES.get(k, k) if "?" in k else k, na_action="ignore"
        )
        # An empty name is "no crop declared", not a name that failed to map.
        resolved = resolved.replace("", None)

        unresolved = sorted({k for k in resolved[resolved.notna()].unique() if "?" in k})
        assert not unresolved, (
            f"{self.variant}: {len(unresolved)} crop name(s) still contain '?' after the "
            f"alias table: {unresolved}. '?' is a character the provider lost; resolve it "
            f"offline against pt.csv and add it to QUESTION_MARK_ALIASES, or the rows go "
            f"to HCAT with no code at all."
        )

        codes = resolved.map(lookup)
        missing = resolved[codes.isna() & resolved.notna()]
        for name, count in missing.value_counts().items():
            self._unmapped_names[name] = self._unmapped_names.get(name, 0) + int(count)
        return codes

    def _island_ids(self, gdf, name):
        """Synthesise ids for a file the source left without one. See ISLAND_ID_BASE."""
        # The invariant this range depends on: no land occupation the provider numbers can
        # ever reach ISLAND_ID_BASE, so a synthesised id can never be mistaken for or
        # collide with a real one. That is an observation about IFAP's numbering rather
        # than anything the format enforces -- the largest OSA_ID in any edition from 2017
        # to 2025 is 46,449,461, four orders of magnitude below the base -- so it is
        # asserted here rather than left to a comment. Lowering ISLAND_ID_BASE, or reusing
        # this path for a source whose identifiers are larger, then fails loudly instead of
        # silently merging two id namespaces.
        #
        # Only the members read before this one are visible here; post_migrate's duplicate
        # check is the backstop for the rest, since an actual collision would surface there
        # as a repeated id.
        if self._max_published_id is not None:
            assert self._max_published_id < ISLAND_ID_BASE, (
                f"{name}: synthesised island ids start at {ISLAND_ID_BASE:,}, but the "
                f"source has already published the land occupation "
                f"{self._max_published_id:,}. The two id ranges must not overlap: raise "
                f"ISLAND_ID_BASE above every published OSA_ID, or the synthesised ids and "
                f"the provider's own share a namespace."
            )

        point = gdf.geometry.representative_point()
        order = pd.DataFrame(
            {"par": gdf["PAR_NUM"].astype("string"), "x": point.x, "y": point.y}
        ).sort_values(["par", "x", "y"], kind="stable")
        ids = pd.Series(
            range(
                ISLAND_ID_BASE + self._island_rows, ISLAND_ID_BASE + self._island_rows + len(gdf)
            ),
            index=order.index,
            dtype="int64",
        )
        self._island_rows += len(gdf)
        self.info(
            f"{name}: {len(gdf):,} rows with no OSA_ID, ids synthesised from "
            f"{ISLAND_ID_BASE:,} by stable sort on (PAR_NUM, x, y)"
        )
        return ids.reindex(gdf.index)

    def _perimeter_metres(self, geometry):
        """Perimeter in metres, measured in each feature's own UTM zone.

        A conformal projection is what length needs, and one zone will not do: Portugal
        spans UTM 25N to 29N, and while 95% of fields are in 29N on the mainland, the
        Azores fall in 25N and 26N and Madeira in 28N. Measured over a whole edition that
        is 4.8% of features that a single-zone choice would get wrong.

        This is not something the base converter can be left to do. It measures lengths in
        UTM only for the parts of features it has split out of a multipolygon, not for
        every row, so it does not produce metrics:perimeter in the general case at all.
        And where it does run it calls estimate_utm_crs() once for the whole set, which
        returns a single zone -- exactly the choice that is wrong for 4.8% of Portugal.
        Any country spanning more than one zone has the same problem.
        """
        x = geometry.representative_point().x.to_numpy(dtype="float64")
        # 2019 publishes 55 features with no geometry at all, and this runs in migrate,
        # before the base converter drops them. Their zone is undefined, so they keep a
        # NaN perimeter and are dropped a few steps later regardless.
        located = np.isfinite(x)
        # Portugal is entirely in the northern hemisphere, so the 326xx band applies.
        epsg = np.zeros(len(x), dtype="int64")
        epsg[located] = 32600 + (np.floor((x[located] + 180) / 6) + 1).astype("int64")

        # Positional throughout: read_data concatenates the regional frames without
        # reindexing, so the labels repeat and a label-based assignment would misalign.
        out = np.full(len(x), np.nan, dtype="float64")
        for code in np.unique(epsg[located]):
            in_zone = epsg == code
            out[in_zone] = geometry[in_zone].to_crs(f"EPSG:{int(code)}").length.to_numpy()
        counts = ", ".join(
            f"EPSG:{int(c)} {int((epsg == c).sum()):,}" for c in np.unique(epsg[located])
        )
        missing = int((~located).sum())
        self.info(
            f"Perimeter measured per UTM zone ({counts})"
            + (f"; {missing:,} row(s) without a geometry left unmeasured" if missing else "")
        )
        return out

    def migrate(self, gdf) -> gpd.GeoDataFrame:
        # 2025 renamed the crop code column and dropped the crop name.
        if "PUN_CUL_CO" in gdf.columns:
            gdf = gdf.rename(columns={"PUN_CUL_CO": "CUL_CODIGO"})

        # 2017-2019 publish the crop as a Portuguese name rather than a code, so the name
        # is kept as crop:name -- these are the only editions besides 2023 that publish one
        # -- and resolved to a code here, before AddHCATMixin reads it in post_migrate.
        if self.variant in NAME_EDITIONS and "C1" in gdf.columns:
            names = gdf["C1"]
            gdf["CT_português"] = names
            gdf["C1"] = self._crop_codes(names)

        # 2020-2022 carry up to twelve crops per land occupation in C1..C12. C1 is the
        # primary one and holds the same three-digit code CUL_CODIGO holds elsewhere
        # (111 of 113 distinct values sampled in 2021 are in pt.csv).
        if "CUL_CODIGO" not in gdf.columns and "C1" in gdf.columns:
            gdf = gdf.rename(columns={"C1": "CUL_CODIGO"})

        # 2020-2022 publish the land occupation polygon itself rather than the crop parcels
        # inside it, so they carry no CUL_ID: the occupation is the field, and the parcel
        # that contains it (PAR_ID) is its block -- the same relationship 2023 and 2025
        # express as CUL_ID inside OSA_ID. Provisional, pending IFAP confirmation that
        # `id` should mean the crop parcel in every edition; delete this line to revert.
        if "CUL_ID" not in gdf.columns and "OSA_ID" in gdf.columns:
            gdf = gdf.rename(columns={"OSA_ID": "CUL_ID", "PAR_ID": "OSA_ID"})

        if gdf.crs is not None and gdf.crs.is_geographic:
            # 2025 is published in WGS 84, with Shape_Area and Shape_Length computed in
            # degrees. Recompute both in metres; up to 2023 the file is in ETRS89 /
            # Portugal TM06 and the published values are already metric. 2020-2022 are
            # reprojected to WGS 84 in file_migration and land here too: 2020 and 2021
            # publish no area at all, and for 2022 the recomputed values differ from the
            # provider's by 0.02% over the country (0.05% at worst, in the Azores).
            #
            # Area and length need different projections. EPSG:6933 is equal-area, so it
            # is right for area and wrong for length: measured against UTM over 100,000
            # polygons per edition it puts a third of every edition more than 5% out, with
            # a signed spread from -10% to +12% depending on how a polygon is oriented.
            gdf["Shape_Area"] = gdf.geometry.to_crs("EPSG:6933").area
            gdf["Shape_Length"] = self._perimeter_metres(gdf.geometry)

        # 2017-2019 leave the crop NULL where the source published no crop column, published
        # a NULL value (the common case), or used a name pt.csv does not carry: together
        # 22.85%, 18.72% and 20.94% of the three editions.
        #
        # None of it can be written as NULL. crop:code is required in the crop extension,
        # so the Parquet field is built nullable=False and pyarrow refuses the write. On
        # this base nothing objects earlier, because vecorel-cli 0.2.17 has no drop guard
        # at all; from 0.2.18 BaseConverter._drop_incomplete_rows covers crop:code via
        # CUL_CODIGO and raises above max_dropped_share, 1% by default. So on no version
        # are these rows silently lost: the empty string is used because NULL cannot be
        # written, not to avoid a silent loss. See harmonized-field-data-catalog#21, whose
        # proposed fix of writing NULL needs the crop extension changed first.
        #
        # The earlier editions are not uniform: 2020-2022 use the empty string, 2023 a
        # single space, 2025 neither. An audit covering all of them needs .strip().
        # Applied after the rename so it covers the resolved column.
        if self.variant in NAME_EDITIONS and "CUL_CODIGO" in gdf.columns:
            blank = int(gdf["CUL_CODIGO"].isna().sum())
            if blank:
                self.info(f"{blank:,} row(s) with no crop code -> '' (as in 2020-2022)")
                gdf["CUL_CODIGO"] = gdf["CUL_CODIGO"].fillna("")
            if "CT_português" in gdf.columns:
                gdf["CT_português"] = gdf["CT_português"].fillna("")

        # 2025 types the identifiers as floats, which would stringify id as "28398800.0";
        # so does 2021's crop table, and 2020-2022's PAR_ID.
        for column in ("OSA_ID", "CUL_ID"):
            if column in gdf.columns and gdf[column].dtype.kind == "f":
                gdf[column] = gdf[column].astype("int64")

        return super().migrate(gdf)

    def _load_crop_table(self, folder):
        """The campaign's crop table, keyed by land-occupation id and verified unique."""
        if self._crop_table is not None:
            return self._crop_table

        path = os.path.join(folder, CROP_TABLE[self.variant])
        fields = list(pyogrio.read_info(path)["fields"])
        key = next(f for f in fields if f.lower() == "osa_id")
        self.info(f"Reading crop table {os.path.basename(path)} (key column '{key}')")
        df = pyogrio.read_dataframe(path, columns=[key, "C1"], read_geometry=False)
        df = df.rename(columns={key: "OSA_ID"})

        # Culturas_2021.dbf carries 14 identical rows keyed on Osa_id = 0, every crop
        # column NULL, and no geometry in the edition uses that id (checked across all
        # 4,882,078 features of its 8 regional files). Drop keys no field can use rather
        # than weaken the uniqueness assertion below, which is the only thing standing
        # between a duplicated key and a silently inflated edition.
        df = df[df["OSA_ID"] != 0]

        col = df["OSA_ID"]
        assert col.notna().all(), f"{int(col.isna().sum())} rows in {path} have no {key}"
        if col.dtype.kind == "f":
            # 2021 types the key as a float. Integers are exact in float64 well past these
            # values, but cast explicitly and prove nothing was lost rather than letting a
            # 1.23e+08 reach the join.
            assert (col % 1 == 0).all(), f"{key} has fractional values"
            assert col.abs().max() < 2**53, f"{key} exceeds the exact float64 integer range"
            df["OSA_ID"] = col.astype("int64")
        dupes = int(df["OSA_ID"].duplicated().sum())
        assert dupes == 0, f"{dupes} duplicate {key} values in {path}: the join would fan out"

        self.info(
            f"Crop table: {len(df):,} rows, key unique, {int(df['C1'].notna().sum()):,} with a code"
        )
        self._crop_table = df
        return df

    def _name_edition_migration(self, gdf, name, crs_before):
        """Per-file step for 2017-2019: one crop column, ids, and the 2018 duplicate."""
        # The crop columns are found by number, because the count varies per file, the
        # case is mixed inside one year and the range can skip a value. Only the first is
        # carried, matching 2020-2022, where C1 is the primary crop of the occupation.
        numbered = {}
        for column in gdf.columns:
            match = CROP_COLUMN.match(str(column))
            if match:
                numbered[int(match.group(1))] = column
        if numbered:
            primary = numbered[min(numbered)]
            if primary != "C1":
                gdf = gdf.rename(columns={primary: "C1"})
            self.info(
                f"{name}: {len(numbered)} crop column(s) {sorted(numbered)}, primary '{primary}'"
            )
        else:
            # 2017's two island files and 2018's Azores file publish no crop at all.
            self.info(f"{name}: no crop column, crop:code will be empty")
            gdf["C1"] = None

        # The block is PAR_NUM here, a 13-digit numeric string, rather than the PAR_ID
        # float of 2020-2022. Naming it PAR_ID lets migrate's existing rename carry it to
        # block_id unchanged; the cast is explicit because block_id is declared int64.
        if "PAR_NUM" in gdf.columns:
            gdf["PAR_ID"] = gdf["PAR_NUM"].astype("int64")

        if "OSA_ID" in gdf.columns:
            published = gdf["OSA_ID"].astype("int64")
            self._max_published_id = max(self._max_published_id or 0, int(published.max()))
        else:
            gdf["OSA_ID"] = self._island_ids(gdf, name)

        rows = len(gdf)
        overlaps = OVERLAPPING_MEMBERS.get(self.variant, {})
        ids = gdf["OSA_ID"].astype("int64")
        gdf["OSA_ID"] = ids
        clash = ids[ids.isin(self._seen_ids)]
        if len(clash):
            expected = overlaps.get(name)
            sources = sorted({self._seen_ids[i] for i in clash.unique()})
            assert expected is not None and sources == [expected], (
                f"{name}: {len(clash):,} OSA_ID(s) already published by {sources}. Only "
                f"2018's Norte_S is known to repeat another member; an overlap anywhere "
                f"else means two members cover the same fields and the edition would be "
                f"inflated by that many rows."
            )
            gdf = gdf[~ids.isin(self._seen_ids)]
            self.info(
                f"{name}: dropped {len(clash):,} row(s) duplicating {expected} "
                f"({rows:,} -> {len(gdf):,})"
            )

        self._seen_ids.update(dict.fromkeys(gdf["OSA_ID"].tolist(), name))
        self._regions.append((name, len(gdf), None))
        self.info(f"{name}: {len(gdf):,} features, CRS {crs_before} -> EPSG:4326")
        return gdf[[c for c in KEEP if c in gdf.columns]]

    def file_migration(self, gdf, path, uri, layer):
        if self.variant not in MEMBERS:
            return gdf

        # OVERLAPPING_MEMBERS is keyed on the layer name, which for a shapefile is the
        # basename without its extension. layer is always set for these editions, so the
        # fallback never runs today, but it would return "<stem>.shp" and silently miss
        # the key; strip the extension so the two can never disagree.
        name = layer or os.path.splitext(os.path.basename(path))[0]
        crs_before = gdf.crs.name if gdf.crs else None
        # The regions arrive in different projections -- the mainland in ETRS89 / Portugal
        # TM06, Madeira and the two Azores groups each in their own UTM zone -- so they have
        # to agree before pd.concat puts them in one frame, or the coordinates are silently
        # mixed. WGS 84 is what 2025 publishes.
        gdf = gdf.to_crs("EPSG:4326")

        if self.variant in NAME_EDITIONS:
            return self._name_edition_migration(gdf, name, crs_before)

        rows = len(gdf)
        if self.variant in CROP_TABLE:
            assert "OSA_ID" in gdf.columns, f"{name} has no OSA_ID to join on"
            key = gdf["OSA_ID"]
            if key.dtype.kind == "f":
                assert (key.dropna() % 1 == 0).all(), f"{name}: fractional OSA_ID"
            gdf["OSA_ID"] = key.astype("int64")
            crops = self._load_crop_table(os.path.dirname(path))
            # many_to_one makes pandas raise if the crop table is not unique on the key,
            # so a silent one-to-many fan-out cannot inflate the edition here.
            gdf = gdf.merge(crops, on="OSA_ID", how="left", validate="many_to_one")
            assert len(gdf) == rows, f"{name}: join changed row count {rows} -> {len(gdf)}"
            matched = int(gdf["C1"].notna().sum())
            self.info(
                f"{name}: {rows:,} features, {matched:,} joined to a crop code "
                f"({rows - matched:,} unmatched), CRS {crs_before} -> EPSG:4326"
            )
        else:
            matched = None
            self.info(f"{name}: {rows:,} features, CRS {crs_before} -> EPSG:4326")
        self._regions.append((name, rows, matched))

        # 2020-2022 leave the crop NULL where none was declared; it cannot be written that
        # way, for the reasons in migrate(). Measured on the published editions this is
        # 1,590,200 of 4,766,789 rows in 2020, 1,446,358 of 4,882,314 in 2021 and
        # 1,458,102 of 4,953,834 in 2022.
        if "C1" in gdf.columns:
            blank = int(gdf["C1"].isna().sum())
            if blank:
                self.info(f"{name}: {blank:,} rows with no crop code -> ''")
                gdf["C1"] = gdf["C1"].fillna("")

        return gdf[[c for c in KEEP if c in gdf.columns]]

    def post_migrate(self, gdf):
        if self._regions:
            self.info(
                f"Merged {len(self._regions)} regional file(s), "
                f"{sum(r for _, r, _ in self._regions):,} features total"
            )
        if self._unmapped_names:
            total = sum(self._unmapped_names.values())
            self.info(
                f"{len(self._unmapped_names)} crop name(s) not in pt.csv, {total:,} row(s); "
                f"left without a code rather than guessed at. Most common: "
                + ", ".join(
                    f"{n!r} ({c:,})"
                    for n, c in sorted(self._unmapped_names.items(), key=lambda kv: -kv[1])[:5]
                )
            )
        if self.variant in NAME_EDITIONS:
            # The whole point of the 2018 de-duplication: no two source rows may claim the
            # same land occupation. This runs before the base converter's make_valid() and
            # explode() (base.py:406, after post_migrate at :372), so it sees one row per
            # source feature. A multipart field becomes several rows sharing this id after
            # the explode, which is how every fiboa converter behaves and is not what this
            # guards against -- in 2017 that is 161 ids over 364 rows. What it catches is a
            # member repeating another member's fields, the way 2018's Norte_S repeats
            # 154,980 of Norte_N's.
            ids = gdf["CUL_ID"]
            duplicated = int(ids.duplicated().sum())
            assert duplicated == 0, (
                f"{self.variant}: {duplicated:,} source row(s) share a land occupation id "
                f"before the geometry explode, so two members cover the same fields"
            )
        return super().post_migrate(gdf)
