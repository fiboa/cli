from fiboa_cli.conversion.converter_rest import EsriRESTConverterMixin
from fiboa_cli.datasets.es_base import ESBaseConverter


class ESGAConverter(EsriRESTConverterMixin, ESBaseConverter):
    id = "es_ga"
    short_name = "Spain "
    title = "Spain Galicia Crop fields"
    description = """
**Galician Crop Fields**: The Geographic Information System for Agricultural Plots (SIXPAC) is an official reference database for the identification of agricultural plots, which is mandatory in Spain for making applications for direct CAP aid that require declaring surface areas.
SIXPAC information is relevant to farmers applying for these aid schemes, so that they can indicate the location of the farm surfaces that may be eligible for subsidies, as well as to facilitate the submission of requests for changes to data relating to land uses contained in the system.
    """
    license = "CC-BY-4.0"  # https://mapas.xunta.gal/gl/aviso-legal
    attribution = "Información procedente do FOGGA"
    provider = "Virtual Office for Rural Environment <https://ovmediorural.xunta.gal/es/consultas-publicas/sixpac>"
    columns = {
        "DN_OID": "id",
        "geometry": "geometry",
        "PROVINCIA": "admin_province_code",
        "MUNICIPIO": "admin_municipality_code",
        "DN_SURFACE": "metrics:area",
        "USO_SIGPAC": "crop:code",
        "crop:name": "crop:name",
        "crop:name_en": "crop:name_en",
    }
    area_is_in_ha = False
    missing_schemas = {
        "properties": {
            "admin_province_code": {"type": "string"},
            "admin_municipality_code": {"type": "string"},
        }
    }

    # ideg.xunta.gal serves one MapServer per campaign, SIXPAC_2014 .. SIXPAC_2026 (as of 2026-09)
    variants = {str(year): str(year) for year in range(2026, 2014 - 1, -1)}
    use_code_attribute = "USO_SIGPAC"
    use_variant_as_determination = True

    rest_base_url = (
        "https://ideg.xunta.gal/servizos/rest/services/ParcelasCatastrais/SIXPAC_{year}/MapServer"
    )

    # The older campaigns name the same things differently:
    #   2014: RECINTO layer, SUP_SIGPAC, no DN_OID (nor AGREGADO)
    #   2015: SUP_SIX / USO_SIX
    #   2020: no DN_OID, but IDGEOM (the geometry id, unique and never null)
    file_renames = {"SUP_SIGPAC": "DN_SURFACE", "SUP_SIX": "DN_SURFACE", "USO_SIX": "USO_SIGPAC"}

    def rest_layer_filter(self, layers):
        return next(layer for layer in layers if "recinto" in layer["name"].lower())

    def file_migration(self, gdf, path, uri, layer):
        gdf = gdf.rename(columns={k: v for k, v in self.file_renames.items() if k in gdf.columns})
        if "DN_OID" not in gdf.columns:
            if "IDGEOM" in gdf.columns:
                gdf["DN_OID"] = gdf["IDGEOM"]
            else:
                # 2014 has no surrogate id at all; the SIGPAC recinto reference is the identifier
                parts = ["PROVINCIA", "MUNICIPIO", "ZONA", "POLIGONO", "PARCELA", "RECINTO"]
                gdf["DN_OID"] = gdf[parts].astype(int).astype(str).agg("-".join, axis=1)
        return gdf

    def get_urls(self):
        if not self.variant:
            self.variant = next(iter(self.variants))
        return {"REST": self.rest_base_url.format(year=self.variant)}
