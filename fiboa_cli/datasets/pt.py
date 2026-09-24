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
# 2021's archive also holds "Culturas_2021", a table without geometry, which DATA_LAYER
# would select.
EDITION_LAYER = {
    "2022": re.compile(r"^Ocupacoes_solo"),
    "2021": re.compile(r"^Ocupacoes_solo_"),
    "2020": re.compile(r"^Subparcelas"),
}

# 2017-2022 ship an archive of regional files, named differently every year. Names with
# accents are globbed, because they extract differently depending on the tool.
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
    # Norte_N must be read before Norte_S, see OVERLAPPING_MEMBERS
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

# 2020 and 2021 publish the crop code in a separate table, keyed by the land occupation.
CROP_TABLE = {"2021": "Culturas_2021.dbf", "2020": "culturas_2020.dbf"}

# 2017-2019 publish the crop as a Portuguese name instead of a code.
NAME_EDITIONS = ("2019", "2018", "2017")

# The crop columns of 2017-2019. Their count, case and numbering vary per file, and the
# range can skip a number, so the primary crop is the lowest number found.
CROP_COLUMN = re.compile(r"^[Cc](\d{1,2})$")

# 2018 publishes 154,980 fields twice, in Norte_N and Norte_S, as exact duplicates.
# Norte_S also has fields of its own, so only the repeated rows are dropped.
OVERLAPPING_MEMBERS = {"2018": ("Ocupacoes_solo_Norte_N", "Ocupacoes_solo_Norte_S")}

# 2017's Azores and Madeira files publish no field id, and PAR_NUM repeats, so ids are
# numbered from here: far above any published OSA_ID (at most ~46 million).
ISLAND_ID_BASE = 10**12

# 2018 replaced an accented letter in some crop names with "?". Each was resolved offline
# to the only pt.csv name it can stand for; an unknown "?" name raises.
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

# The columns each regional file is reduced to, in the layout of 2023: dropping the rest
# before the regions are merged keeps millions of unused strings out of memory.
KEEP = ("geometry", "CUL_ID", "OSA_ID", "CUL_CODIGO", "CT_português")


def normalise_crop_name(value, keep_question_mark=False):
    """Fold a crop name to its comparison key: 2017 spells one crop several ways
    (PRADOS_TEMPORARIOS, PRADOS TEMPORÁRIOS), so accents and separators are dropped."""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(c for c in text if not unicodedata.combining(c)).upper()
    allowed = "A-Z0-9 ?" if keep_question_mark else "A-Z0-9 "
    text = re.sub(f"[^{allowed}]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


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
        # 2017-2019 and 2023 publish a crop name, the other editions only the code
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._crop_table = None
        self._name_to_code = None
        self._kept_ids = set()
        self._island_rows = 0

    def layer_filter(self, layer, uri):
        # 2017-2019 are single-layer shapefiles selected by MEMBERS alone
        if self.variant in NAME_EDITIONS:
            return True
        return bool(EDITION_LAYER.get(self.variant, DATA_LAYER).match(layer))

    def file_migration(self, gdf, path, uri, layer=None):
        if self.variant not in MEMBERS:
            return gdf
        # The regions come in four projections, which must agree before they are merged
        gdf = gdf.to_crs("EPSG:4326")
        if self.variant in NAME_EDITIONS:
            name = layer or os.path.splitext(os.path.basename(path))[0]
            gdf = self._from_name_edition(gdf, name)
        else:
            gdf = self._from_code_edition(gdf, os.path.dirname(path))
        # crop:code is required and cannot be written as null
        gdf["CUL_CODIGO"] = gdf["CUL_CODIGO"].fillna("")
        return gdf[[c for c in KEEP if c in gdf.columns]]

    def _from_code_edition(self, gdf, folder):
        """A regional file of 2020-2022, in the layout of 2023."""
        if self.variant in CROP_TABLE:
            gdf["OSA_ID"] = gdf["OSA_ID"].astype("int64")
            crops = self._load_crop_table(folder)
            gdf = gdf.merge(crops, on="OSA_ID", how="left", validate="many_to_one")
        # No crop parcels are published: the land occupation is the field and its
        # parcel the block, as CUL_ID lies in OSA_ID in 2023 and 2025.
        return gdf.rename(columns={"C1": "CUL_CODIGO", "OSA_ID": "CUL_ID", "PAR_ID": "OSA_ID"})

    def _load_crop_table(self, folder):
        if self._crop_table is None:
            path = os.path.join(folder, CROP_TABLE[self.variant])
            # 2021 spells the key Osa_id and types it as a float
            key = next(f for f in pyogrio.read_info(path)["fields"] if f.lower() == "osa_id")
            df = pyogrio.read_dataframe(path, columns=[key, "C1"], read_geometry=False)
            df = df.rename(columns={key: "OSA_ID"})
            # 2021 has 14 empty rows keyed 0, which no field uses
            self._crop_table = df[df["OSA_ID"] != 0].astype({"OSA_ID": "int64"})
        return self._crop_table

    def _from_name_edition(self, gdf, name):
        """A regional file of 2017-2019, in the layout of 2023."""
        numbered = {int(m[1]): c for c in gdf.columns if (m := CROP_COLUMN.match(str(c)))}
        crop = gdf[numbered[min(numbered)]] if numbered else pd.Series(None, index=gdf.index)
        gdf["CT_português"] = crop
        gdf["CUL_CODIGO"] = self._crop_codes(crop)

        if "OSA_ID" in gdf.columns:
            gdf["CUL_ID"] = gdf["OSA_ID"].astype("int64")
        else:
            gdf["CUL_ID"] = self._island_ids(gdf)
        # the block, a 13-digit numeric string
        gdf["OSA_ID"] = gdf["PAR_NUM"].astype("int64")

        kept, repeated = OVERLAPPING_MEMBERS.get(self.variant, (None, None))
        if name == kept:
            self._kept_ids = set(gdf["CUL_ID"])
        elif name == repeated:
            gdf = gdf[~gdf["CUL_ID"].isin(self._kept_ids)]
        return gdf

    def _island_ids(self, gdf):
        """Number the fields of a file without ids in a stable order: PAR_NUM, then the
        position of the field, then the order of the records in the file."""
        point = gdf.geometry.representative_point()
        order = pd.DataFrame(
            {"par": gdf["PAR_NUM"].astype("string"), "x": point.x, "y": point.y}
        ).sort_values(["par", "x", "y"], kind="stable")
        start = ISLAND_ID_BASE + self._island_rows
        self._island_rows += len(gdf)
        ids = pd.Series(range(start, start + len(gdf)), index=order.index, dtype="int64")
        return ids.reindex(gdf.index)

    def _crop_codes(self, names):
        """Resolve crop names to pt.csv codes, which HCAT is mapped from."""
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
        """pt.csv original_name -> original_code, keyed by the normalised name."""
        if self._name_to_code is None:
            # also used by AddHCATMixin, which then does not load the list again
            if self.ec_mapping is None:
                self.ec_mapping = load_ec_mapping(self.ec_mapping_csv, url=self.mapping_file)
            lookup = {}
            for entry in self.ec_mapping:
                key = normalise_crop_name(entry["original_name"])
                code = entry["original_code"]
                # POUSIO is 089 and 89, one code padded two ways; the padded one wins.
                if key not in lookup or code < lookup[key]:
                    lookup[key] = code
            # AZEVEM is 067 (ryegrass) and 076 (lolium), which only differ in the
            # English name and share the HCAT code; ryegrass is the common name.
            lookup["AZEVEM"] = "067"
            self._name_to_code = lookup
        return self._name_to_code

    def migrate(self, gdf) -> gpd.GeoDataFrame:
        # 2025 renamed the crop code column and dropped the crop name.
        if "PUN_CUL_CO" in gdf.columns:
            gdf = gdf.rename(columns={"PUN_CUL_CO": "CUL_CODIGO"})

        # 2025 is published in WGS 84 with Shape_Area and Shape_Length in degrees, and
        # 2017-2022 are reprojected to it in file_migration. The area is measured by the
        # base converter (area_calculate_missing); up to 2023 the source values are metric.
        if gdf.crs is not None and gdf.crs.is_geographic:
            gdf = gdf.drop(columns=["Shape_Area"], errors="ignore")
            gdf["Shape_Length"] = self._perimeter_metres(gdf.geometry)

        # 2020-2022 and 2025 type the identifiers as floats, which would stringify as "1.0"
        for column in ("OSA_ID", "CUL_ID"):
            if column in gdf.columns and gdf[column].dtype.kind == "f":
                gdf[column] = gdf[column].astype("int64")

        return super().migrate(gdf)

    @staticmethod
    def _perimeter_metres(geometry):
        """Perimeter in metres, in each feature's own UTM zone.

        The equal-area EPSG:6933 distorts lengths by up to ±10%, and Portugal spans UTM
        zones 25N to 29N (the Azores and Madeira), so no single zone fits either.
        """
        x = geometry.representative_point().x.to_numpy(dtype="float64")
        # rows without a geometry (55 in 2019) stay NaN; the base converter drops them
        located = np.isfinite(x)
        zones = np.zeros(len(x), dtype="int64")
        zones[located] = 32600 + (np.floor((x[located] + 180) / 6) + 1).astype("int64")
        out = np.full(len(x), np.nan)
        for zone in np.unique(zones[located]):
            in_zone = zones == zone
            out[in_zone] = geometry[in_zone].to_crs(f"EPSG:{zone}").length.to_numpy()
        return out
