import math
from pathlib import Path

import numpy as np
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter


class Converter(AdminConverterMixin, FiboaBaseConverter):
    _sources = [
        "Algodao/GO/ALGODAO_GO_Safra_2019_2020.zip",
        "Algodao/GO/ALGODAO-GO_Safra_2018_2019.zip",
        "Algodao/GO/GO_ALGODAO_2021.zip",
        "Algodao/GO/GO_ALGODAO_2223.zip",
        "Algodao/MS/MS_ALGODAO_2021.zip",
        "Algodao/MS/MS_ALGODAO_2122.zip",
        "Arroz_Irrigado/GO/GO_ARROZ_IRRIG_2122.zip",
        "Arroz_Irrigado/GO/GO_ARROZ_IRRIG_INUND_2324.zip",
        "Arroz_Irrigado/GO/ARROZ-GO_Safra_2018_2019.zip",
        "Arroz_Irrigado/MS/ARROZ-MS_Safra_2018_2019.zip",
        "Arroz_Irrigado/PR/ARROZ-PR_Safra_2017_2018.zip",
        "Arroz_Irrigado/RS/ARROZ-RS_Safra_2019_2020.zip",
        "Arroz_Irrigado/SC/ARROZ-SC_Safra_2018_2019.zip",
        "Arroz_Irrigado/TO/ARROZ-TO_Safra_2017_2018.zip",
        "Arroz_Irrigado/GO/GO_ARROZ_IRRIG_INUND_2324.zip",
        "Arroz_Irrigado/TO/TO_ARROZ_IRRIG_2324.zip",
        "Cana/GO/CANA-GO_Safra_2011_2012.zip",
        "Cafe/BA/CAFE-BA_Safra_2019.zip",
        "Cafe/DF/CAFE-DF_Safra_2018.zip",
        "Cafe/GO/CAFE-GO_Safra_2018.zip",
        "Cafe/GO/CAFE-GO_Safra_2019.zip",
        "Cafe/PR/CAFE-PR_Safra_2017.zip",
        "Cafe/MG/CAFE-MG_Safra_2017.zip",
        "Cafe/DF/DF_CAFE_24.zip",
        "Cafe/DF/DF_CAFE_24.zip",
        "Cafe/GO/GO_CAFE_21.zip",
        "Cafe/RJ/RJ_CAFE_21.zip",
        "Culturas_de_Verao_1_Safra/DF/CV-DF_Safra_2013_2014.zip",
        "Culturas_de_Verao_1_Safra/DF/CV-DF_Safra_2014_2015.zip",
        "Culturas_de_Verao_1_Safra/DF/CV-DF_Safra_2017_2018.zip",
        "Culturas_de_Verao_1_Safra/TO/CV-TO_Safra_2019_2020.zip",
    ]
    sources = {
        "https://portaldeinformacoes.conab.gov.br/downloads/mapas/" + k: ["*.shp"] for k in _sources
    }
    id = "br_conab"
    short_name = "Conab"
    title = "Brazil Crop Fields (CONAB)"
    description = """
    CONAB, Brazil's National Supply Company, is the government agency responsible for providing information on the country's agricultural harvest.

    This subset of 27, after inspecting all boundaries in the CONAB public database, appear to be hand-drawn field boundaries.

    The content of the Mappings comes from Conab, total or partial reproduction without profit motives is authorized,
    as long as the source is cited and the integrity of the information is maintained.

    Further information or suggestions can be sent to the email address conab.geote@conab.gov.br
    """
    providers = [
        {
            "name": "Conab",
            "url": "https://portaldeinformacoes.conab.gov.br/mapeamentos-agricolas-downloads.html",
            "roles": ["producer", "licensor"],
        }
    ]
    attribution = "CONAB - conab.gov.br"
    license = "CC-BY-NC-4.0"
    columns = {
        "geometry": "geometry",
        "id": "id",
        "cd_mun": "admin_municipality_code",
        "nm_mun": "admin_municipality_name",
        "area_ha": "metrics:area",
    }

    missing_schemas = {
        "properties": {
            "admin_municipality_code": {"type": "string"},
            "admin_municipality_name": {"type": "string"},
        }
    }

    def file_migration(self, gdf, path, uri, layer=None):
        gdf = super().file_migration(gdf, path, uri, layer)
        # Create unique IDs
        name = Path(path).stem
        gdf["id"] = name + "_" + gdf.index.astype(str)
        # Harmonize projection or pd.concat will fail
        if gdf.crs.srs != "EPSG:4674":
            gdf.to_crs(crs="EPSG:4674", inplace=True)
        return gdf

    def migrate(self, gdf):
        gdf = gdf.reset_index(drop=True)
        gdf["area_ha"].combine_first(gdf["Hectares"]).replace(np.nan, None, inplace=True)
        gdf.loc[gdf["area_ha"] == 0, "area_ha"] = None
        gdf["cd_mun"] = gdf["cd_mun"].combine_first(gdf["CD_MUN"]).apply(fformat)
        gdf["nm_mun"] = gdf["nm_mun"].combine_first(gdf["NM_MUN"]).combine_first(gdf["NM_MUNIC"])
        return gdf

    def get_data(self, paths, **kwargs):
        # Set invalid geometries to None in Cafe/MG/CAFE-MG_Safra_2017.zip
        kwargs["on_invalid"] = "warn"
        return super().get_data(paths, **kwargs)


def fformat(x):
    if isinstance(x, float) and not math.isnan(x):
        return f"{x:.0f}"
    return x or None
