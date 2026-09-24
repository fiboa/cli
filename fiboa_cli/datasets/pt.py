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
# 2021 also has "Culturas_2021", a table without geometry, which DATA_LAYER would select
EDITION_LAYER = {
    "2022": re.compile(r"^Ocupacoes_solo"),
    "2021": re.compile(r"^Ocupacoes_solo_"),
    "2020": re.compile(r"^Subparcelas"),
}

# Accented names are globbed: they extract differently depending on the tool
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
}

# 2020 and 2021 publish the crop code in a separate table
CROP_TABLE = {"2021": "Culturas_2021.dbf", "2020": "culturas_2020.dbf"}

# 2017-2019 publish crop names instead of codes
NAME_EDITIONS = ("2019", "2018", "2017")

# Count, case and numbering of the crop columns vary per file; the lowest is the primary crop
CROP_COLUMN = re.compile(r"^[Cc](\d{1,2})$")

# 2018 publishes 154,980 fields in both files; Norte_S also has fields of its own
OVERLAPPING_MEMBERS = {"2018": ("Ocupacoes_solo_Norte_N", "Ocupacoes_solo_Norte_S")}

# 2017's island files publish no field id; numbered from here, far above any OSA_ID (~46M)
ISLAND_ID_BASE = 10**12

# 2018 replaced accented letters in some crop names with "?", resolved offline against pt.csv
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

# Dropping the other columns per file keeps millions of unused strings out of memory
KEEP = ("geometry", "OSA_ID", "PAR_ID", "PAR_NUM", "C1", "member")


def normalise_crop_name(value, keep_question_mark=False):
    """Accents and separators vary within an edition (PRADOS_TEMPORARIOS, PRADOS TEMPORÁRIOS)"""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(c for c in text if not unicodedata.combining(c)).upper()
    allowed = "A-Z0-9 ?" if keep_question_mark else "A-Z0-9 "
    text = re.sub(f"[^{allowed}]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def read_crop_table(path):
    # 2021 spells the key Osa_id and types it as a float
    key = next(f for f in pyogrio.read_info(path)["fields"] if f.lower() == "osa_id")
    df = pyogrio.read_dataframe(path, columns=[key, "C1"], read_geometry=False)
    df = df.rename(columns={key: "OSA_ID"})
    # 2021 has 14 empty rows keyed 0, which no field uses
    return df[df["OSA_ID"] != 0].astype({"OSA_ID": "int64"})


def perimeter_metres(geometry):
    """Measured in each feature's UTM zone: EPSG:6933 distorts lengths by up to ±10% and
    Portugal spans zones 25N to 29N."""
    x = geometry.representative_point().x.to_numpy(dtype="float64")
    # rows without a geometry stay NaN; the base converter drops them
    located = np.isfinite(x)
    zones = np.zeros(len(x), dtype="int64")
    zones[located] = 32600 + (np.floor((x[located] + 180) / 6) + 1).astype("int64")
    out = np.full(len(x), np.nan)
    for zone in np.unique(zones[located]):
        in_zone = zones == zone
        out[in_zone] = geometry[in_zone].to_crs(f"EPSG:{zone}").length.to_numpy()
    return out


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
        "CT_português": "crop:name",
        "Shape_Area": "metrics:area",
        "Shape_Length": "metrics:perimeter",
    }
    extensions = {"https://fiboa.org/crop-extension/v0.2.0/schema.yaml"}
    ec_mapping_csv = "https://fiboa.org/code/pt/pt.csv"
    area_is_in_ha = False
    area_calculate_missing = True
    missing_schemas = {
        "properties": {
            "block_id": {"type": "int64"},
        }
    }

    def layer_filter(self, layer, uri):
        # 2017-2019 are single-layer shapefiles selected by MEMBERS alone
        if self.variant in NAME_EDITIONS:
            return True
        return bool(EDITION_LAYER.get(self.variant, DATA_LAYER).match(layer))

    def file_migration(self, gdf, path, uri, layer=None):
        if self.variant not in MEMBERS:
            return gdf
        # the regions come in four projections
        gdf = gdf.to_crs("EPSG:4326")
        gdf["member"] = layer or os.path.splitext(os.path.basename(path))[0]
        if self.variant in NAME_EDITIONS:
            numbered = {int(m[1]): c for c in gdf.columns if (m := CROP_COLUMN.match(str(c)))}
            if numbered:
                gdf = gdf.rename(columns={numbered[min(numbered)]: "C1"})
        return gdf[[c for c in KEEP if c in gdf.columns]]

    def read_data(self, paths, **kwargs):
        gdf = super().read_data(paths, **kwargs)
        if self.variant in CROP_TABLE:
            crops = read_crop_table(
                os.path.join(os.path.dirname(paths[0][0]), CROP_TABLE[self.variant])
            )
            gdf["OSA_ID"] = gdf["OSA_ID"].astype("int64")
            gdf = gdf.merge(crops, on="OSA_ID", how="left", validate="many_to_one")
        return gdf

    def migrate(self, gdf) -> gpd.GeoDataFrame:
        # 2025 renamed the crop code column and dropped the crop name.
        if "PUN_CUL_CO" in gdf.columns:
            gdf = gdf.rename(columns={"PUN_CUL_CO": "CUL_CODIGO"})

        if self.variant in MEMBERS:
            gdf = self._to_2023_layout(gdf)

        # Shape_* are in degrees: 2025 is published in WGS 84, 2017-2022 are reprojected to it.
        # The base converter measures the area (area_calculate_missing).
        if gdf.crs is not None and gdf.crs.is_geographic:
            gdf = gdf.drop(columns=["Shape_Area"], errors="ignore")
            gdf["Shape_Length"] = perimeter_metres(gdf.geometry)

        # float ids would stringify as "1.0"
        for column in ("OSA_ID", "CUL_ID"):
            if column in gdf.columns and gdf[column].dtype.kind == "f":
                gdf[column] = gdf[column].astype("int64")

        return super().migrate(gdf)

    def _to_2023_layout(self, gdf):
        if self.variant in NAME_EDITIONS:
            gdf = self._from_name_edition(gdf)
        else:
            # no crop parcels are published: the land occupation is the field, its parcel the block
            gdf = gdf.rename(columns={"C1": "CUL_CODIGO", "OSA_ID": "CUL_ID", "PAR_ID": "OSA_ID"})
        # crop:code is required and cannot be written as null
        gdf["CUL_CODIGO"] = gdf["CUL_CODIGO"].fillna("")
        return gdf.drop(columns="member")

    def _from_name_edition(self, gdf):
        kept, repeated = OVERLAPPING_MEMBERS.get(self.variant, (None, None))
        repeats = (gdf["member"] == repeated) & gdf["OSA_ID"].isin(
            gdf.loc[gdf["member"] == kept, "OSA_ID"]
        )
        gdf = gdf[~repeats].copy()

        names = gdf["C1"] if "C1" in gdf.columns else pd.Series(None, index=gdf.index)
        gdf["CT_português"] = names
        gdf["CUL_CODIGO"] = self._crop_codes(names)
        gdf["CUL_ID"] = gdf["OSA_ID"].fillna(self._island_ids(gdf))
        gdf["OSA_ID"] = gdf["PAR_NUM"].astype("int64")
        return gdf

    def _island_ids(self, gdf):
        """Stable order: file, PAR_NUM, position, then record order"""
        islands = gdf[gdf["OSA_ID"].isna()]
        point = islands.geometry.representative_point()
        order = pd.DataFrame(
            {
                "file": islands["member"].map(
                    {os.path.splitext(m)[0]: i for i, m in enumerate(MEMBERS[self.variant])}
                ),
                "par": islands["PAR_NUM"].astype("string"),
                "x": point.x,
                "y": point.y,
            }
        ).sort_values(["file", "par", "x", "y"], kind="stable")
        return pd.Series(range(ISLAND_ID_BASE, ISLAND_ID_BASE + len(order)), index=order.index)

    def _crop_codes(self, names):
        keys = names.map(
            lambda v: normalise_crop_name(v, keep_question_mark=True), na_action="ignore"
        )
        keys = keys.map(lambda k: QUESTION_MARK_ALIASES.get(k, k), na_action="ignore")
        keys = keys.replace("", None)
        unresolved = sorted({k for k in keys.dropna() if "?" in k})
        assert not unresolved, (
            f"{self.variant}: crop names with an unknown '?': {unresolved}. "
            f"Resolve them against pt.csv and add them to QUESTION_MARK_ALIASES."
        )
        return keys.map(self._crop_name_lookup())

    def _crop_name_lookup(self):
        # shared with AddHCATMixin, which then does not load it again
        if self.ec_mapping is None:
            self.ec_mapping = load_ec_mapping(self.ec_mapping_csv, url=self.mapping_file)
        lookup = {}
        for entry in self.ec_mapping:
            key = normalise_crop_name(entry["original_name"])
            code = entry["original_code"]
            # POUSIO is 089 and 89: the padded code wins
            if key not in lookup or code < lookup[key]:
                lookup[key] = code
        # AZEVEM is 067 (ryegrass) and 076 (lolium), which share the HCAT code
        lookup["AZEVEM"] = "067"
        return lookup
