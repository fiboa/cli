import os
import re

import geopandas as gpd
import pyogrio
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin

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
        "2019": BASE + "2017-2020/2019.zip",
        "2018": BASE + "2017-2020/2018.zip",
        "2017": BASE + "2017-2020/2017.zip",
        "2016": BASE + "2011_2016/2016.zip",
        "2015": BASE + "2011_2016/2015.zip",
        # ...
    }

    def layer_filter(self, layer, uri):
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

    def migrate(self, gdf) -> gpd.GeoDataFrame:
        # 2025 renamed the crop code column and dropped the crop name.
        if "PUN_CUL_CO" in gdf.columns:
            gdf = gdf.rename(columns={"PUN_CUL_CO": "CUL_CODIGO"})

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
            metric = gdf.geometry.to_crs("EPSG:6933")
            gdf["Shape_Area"] = metric.area
            gdf["Shape_Length"] = metric.length

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

    def file_migration(self, gdf, path, uri, layer):
        if self.variant not in MEMBERS:
            return gdf

        name = layer or os.path.basename(path)
        crs_before = gdf.crs.name if gdf.crs else None
        # The regions arrive in different projections -- the mainland in ETRS89 / Portugal
        # TM06, Madeira and the two Azores groups each in their own UTM zone -- so they have
        # to agree before pd.concat puts them in one frame, or the coordinates are silently
        # mixed. WGS 84 is what 2025 publishes.
        gdf = gdf.to_crs("EPSG:4326")

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

        # 2023 and 2025 spell "no crop was declared for this field" as an empty string and
        # keep the field; 2020-2022 use NULL. Left as NULL the base converter's
        # REQUIRED_NON_NULL guard drops the rows, which in 2022 means 1,458,049 of
        # 4,953,618 real field boundaries (29.4%, confirmed against the source layers).
        if "C1" in gdf.columns:
            blank = int(gdf["C1"].isna().sum())
            if blank:
                self.info(f"{name}: {blank:,} rows with no crop code -> '' (as in 2023)")
                gdf["C1"] = gdf["C1"].fillna("")

        return gdf[[c for c in KEEP if c in gdf.columns]]

    def post_migrate(self, gdf):
        if self._regions:
            self.info(
                f"Merged {len(self._regions)} regional file(s), "
                f"{sum(r for _, r, _ in self._regions):,} features total"
            )
        return super().post_migrate(gdf)
