import math
import re
from pathlib import Path

import pandas as pd
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter

MIN_FIELD_AREA = 100  # m²


class Converter(AdminConverterMixin, FiboaBaseConverter):
    # The portal's file list: https://barramento.conab.gov.br/portal-informacao-api/api/v1/download
    _sources = [
        "1784839922_algodao-go-safra-2019-2020.zip",
        "1784839955_algodao-go-safra-2018-2019.zip",
        "1784839890_go-algodao-2021.zip",
        "1784558283_go-algodao-2223.zip",
        "1784840252_ms-algodao-2021.zip",
        "1784840209_ms-algodao-2122.zip",
        "1784840479_go-arroz-irrig-2122.zip",
        "1784840507_go-arroz-irrig-inund-23241.zip",
        "1784840800_arroz-go-safra-2018-2019.zip",
        "1784840902_arroz-ms-safra-2018-2019.zip",
        "1784841005_arroz-pr-safra-2017-2018.zip",
        "1784841189_arroz-rs-safra-2019-2020.zip",
        "1784841407_arroz-sc-safra-2018-2019.zip",
        "1784841526_arroz-to-safra-2017-2018.zip",
        "1784841496_to-arroz-irrig-2324.zip",
        "1785258893_cana-go-11-12.zip",
        "1789672175_cafe-ba-19.zip",
        "1785251263_cafe-df-18.zip",
        "1785251314_cafe-go-18.zip",
        "1785251334_cafe-go-19.zip",
        "1785251366_cafe-pr-17.zip",
        "1787760927_cafe-mg-safra-2017.zip",
        "1785251294_cafe-df-24.zip",
        "1785251350_cafe-go-21.zip",
        "1785251708_cafe-rj-21.zip",
        "1785335351_cv-df-safra-2013-2014.zip",
        "1785335351_cv-df-safra-2014-2015.zip",
        "1785335352_cv-df-safra-2017-2018.zip",
        "1785335410_cv-to-safra-2019-2020.zip",
    ]
    sources = {
        "https://portaldeinformacoes.conab.gov.br/downloads/mapas/" + k: ["*.shp"] for k in _sources
    }
    id = "br_conab"
    short_name = "Conab"
    title = "Brazil Crop Fields (CONAB)"
    description = """
CONAB, Brazil's National Supply Company, is the government agency responsible for providing information on the country's agricultural harvest.

These 29 mappings, after inspecting all boundaries in the CONAB public database, appear to be hand-drawn field boundaries.

The content of the Mappings comes from Conab, total or partial reproduction without profit motives is authorized,
as long as the source is cited and the integrity of the information is maintained.

Further information or suggestions can be sent to the email address conab.geote@conab.gov.br
    """
    provider = (
        "Conab <https://portaldeinformacoes.conab.gov.br/mapeamentos-agricolas-downloads.html>"
    )
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
        # Create unique IDs, without the upload timestamp the portal prefixes to its file names
        name = re.sub(r"^\d+_", "", Path(path).stem)
        gdf["id"] = name + "_" + gdf.index.astype(str)
        # Harmonize projection or pd.concat will fail
        if gdf.crs.srs != "EPSG:4674":
            gdf.to_crs(crs="EPSG:4674", inplace=True)
        return gdf

    def migrate(self, gdf):
        # The mappings carry digitising slivers (a fifth of Minas Gerais coffee); no field is that small
        gdf = gdf[self._measure_area(gdf.geometry) >= MIN_FIELD_AREA].reset_index(drop=True)
        gdf["area_ha"] = first_of(gdf, "area_ha", "Hectares")
        gdf["cd_mun"] = first_of(gdf, "cd_mun", "CD_MUN").apply(fformat)
        gdf["nm_mun"] = first_of(gdf, "nm_mun", "NM_MUN", "NM_MUNIC")
        return super().migrate(gdf)

    def get_data(self, paths, **kwargs):
        # Set invalid geometries to None in Cafe/MG/CAFE-MG_Safra_2017.zip
        kwargs["on_invalid"] = "warn"
        return super().get_data(paths, **kwargs)


def first_of(gdf, *names):
    """The first non-empty value per row among the columns the files name differently."""
    result = pd.Series(None, index=gdf.index, dtype=object)
    for name in names:
        if name in gdf.columns:
            result = result.combine_first(gdf[name])
    return result


def fformat(x):
    if isinstance(x, float) and not math.isnan(x):
        return f"{x:.0f}"
    return x or None
