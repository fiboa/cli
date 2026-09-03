import re

import geopandas as gpd
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.hcat import AddHCATMixin

# Up to 2023 the country is split into "Culturas_<district>" layers, from 2025 into
# "T<NUTS 3 code>" layers. Both files carry other layers too (parcel blocks, land cover,
# an empty "Culturas" container, a non-spatial "Codes" table) that are not field boundaries.
DATA_LAYER = re.compile(r"^(Culturas_.+|T[0-9A-Z]{3})$")


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
        "2022": BASE + "2022/2022.zip",
        "2021": BASE + "2021/2021.zip",
        "2020": BASE + "2017-2020/2020.zip",
        "2019": BASE + "2017-2020/2019.zip",
        "2018": BASE + "2017-2020/2018.zip",
        "2017": BASE + "2017-2020/2017.zip",
        "2016": BASE + "2011_2016/2016.zip",
        "2015": BASE + "2011_2016/2015.zip",
        # ...
    }

    def layer_filter(self, layer, uri):
        return bool(DATA_LAYER.match(layer))

    provider = (
        "IPAP - Instituto de Financiamento da Agricultura e Pescas <https://www.ifap.pt/isip/ows/>"
    )
    license = "No conditions apply <https://inspire.ec.europa.eu/metadata-codelist/ConditionsApplyingToAccessAndUse/noConditionsApply>"
    columns = {
        "geometry": "geometry",
        "OSA_ID": "id",
        "CUL_ID": "block_id",
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

    def migrate(self, gdf) -> gpd.GeoDataFrame:
        # 2025 renamed the crop code column and dropped the crop name.
        if "PUN_CUL_CO" in gdf.columns:
            gdf = gdf.rename(columns={"PUN_CUL_CO": "CUL_CODIGO"})

        if gdf.crs is not None and gdf.crs.is_geographic:
            # 2025 is published in WGS 84, with Shape_Area and Shape_Length computed in
            # degrees. Recompute both in metres; up to 2023 the file is in ETRS89 /
            # Portugal TM06 and the published values are already metric.
            metric = gdf.geometry.to_crs("EPSG:6933")
            gdf["Shape_Area"] = metric.area
            gdf["Shape_Length"] = metric.length

        # 2025 types the identifiers as floats, which would stringify id as "28398800.0".
        for column in ("OSA_ID", "CUL_ID"):
            if column in gdf.columns and gdf[column].dtype.kind == "f":
                gdf[column] = gdf[column].astype("int64")

        return super().migrate(gdf)
