import re

import requests
from vecorel_cli.conversion.admin import AdminConverterMixin
from vecorel_cli.vecorel.extensions import ADMIN_DIVISION

from fiboa_cli.datasets.commons.hcat import AddHCATMixin

from ..conversion.per_file import PerFileBaseConverter


class Converter(AdminConverterMixin, AddHCATMixin, PerFileBaseConverter):
    id = "es"
    short_name = "Spain"
    title = "Spain Declared Crops (Cultivos Declarados SIGPAC)"
    description = """
National declared-crop dataset (Cultivos Declarados SIGPAC) published by the Spanish Agricultural Guarantee Fund
(FEGA) via the unified SIGPAC Hub Cloud portal (sigpac-hubcloud.es). Each record is a declaration line within a
farmer's Single Application (Solicitud Única) for Common Agricultural Policy (CAP) direct payments, mapped onto
SIGPAC cadastral divisions. Data is distributed as one GeoPackage per Spanish province, harmonised across the
country since the 2025 campaign year.

This is a high-value dataset (HVD) under EU Implementing Regulation 2023/138.
    """
    provider = "Fondo Español de Garantía Agraria (FEGA) <https://www.fega.gob.es>"
    attribution = "©FEGA / Ministerio de Agricultura, Pesca y Alimentación"
    license = "CC-BY-4.0"

    variants = {"2025": "2025"}

    # FEGA declared-crop codelist (PARC_PRODUCTO) — separate from the SIGPAC land-use list.
    # Reference list shipped inside each provincial GPKG as the `cod_producto` layer.
    ec_mapping_csv = "https://fiboa.org/code/es/es.csv"

    columns = {
        "geometry": "geometry",
        "id": "id",
        "parcel_id": "parcel_id",
        "provincia": "admin:subdivision_code",
        "dn_surface": "metrics:area",
        "parc_producto": "crop:code",
        "parc_sistexp": "irrigation_system",
    }

    area_is_in_ha = False

    extensions = {
        "https://fiboa.org/crop-extension/v0.2.0/schema.yaml",
        ADMIN_DIVISION,
    }

    column_migrations = {
        "parc_producto": lambda col: col.astype("Int64").fillna(0).astype(str),
        "provincia": lambda col: col.astype("Int64").astype(str).str.zfill(2),
    }

    missing_schemas = {
        "properties": {
            "admin_municipality_code": {"type": "string"},
            "irrigation_system": {"type": "string"},
            "parcel_id": {"type": "string"},
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.variant:
            self.variant = next(iter(self.variants))
        self.column_additions = {
            **self.column_additions,
            "determination:datetime": f"{self.variant}-01-01T00:00:00Z",
        }

    def layer_filter(self, layer: str, uri: str) -> bool:
        # GPKG contains the data layer plus several codelist tables (cod_*) — only read the data.
        return layer == "cultivo_declarado"

    def migrate(self, gdf):
        # The SIGPAC cadastral key identifies the recinto, not the row: a recinto can be
        # declared with several crops, and 2025 has 30,514 keys covering 67,689 rows. So it
        # is the parcel_id, and the id is the key plus the number of the row within it.
        def part(col):
            return gdf[col].astype("Int64").astype(str)

        gdf["parcel_id"] = (
            part("provincia").str.zfill(2)
            + "-"
            + part("municipio")
            + "-"
            + part("agregado")
            + "-"
            + part("zona")
            + "-"
            + part("poligono")
            + "-"
            + part("parcela")
            + "-"
            + part("recinto")
            + "-"
            + part("ld_recinto")
        )

        # The base converter splits multi-part geometries after it has checked the ids, which
        # would break uniqueness again — 21,342 of those keys are one multi-part recinto. Split
        # here instead, with the same three steps, which leaves the base converter nothing to do.
        gdf.geometry = gdf.geometry.make_valid()
        gdf = gdf.explode(index_parts=False)
        gdf = gdf[(gdf.geometry.geom_type == "Polygon") & gdf.geometry.is_valid]
        # the explode repeats the source row labels, which would misalign the assignment below
        gdf = gdf.reset_index(drop=True)

        gdf["id"] = gdf["parcel_id"] + "_" + (gdf.groupby("parcel_id").cumcount() + 1).astype(str)

        # Ten rows of 2025 carry a dn_surface at or below zero, which is not an area.
        # Compute those from the geometry — only those, so the other 17.9M are not
        # reprojected for the sake of ten.
        unusable = gdf["dn_surface"] <= 0
        if unusable.any():
            self.info(f"Computing the area of {unusable.sum()} row(s) with a dn_surface <= 0")
            gdf.loc[unusable, "dn_surface"] = gdf.loc[unusable, "geometry"].to_crs("EPSG:6933").area

        return super().migrate(gdf)

    def get_urls(self):
        if self.variant not in self.variants:
            opts = ", ".join(self.variants.keys())
            raise ValueError(f"Unknown variant '{self.variant}', choose from {opts}")

        year = self.variant
        base = f"https://sigpac-hubcloud.es/geopackages/{year}/cultivo_declarado/"
        response = requests.get(base, timeout=60)
        response.raise_for_status()
        # The directory listing is a classic Apache-style HTML index; parse out the .zip hrefs.
        zip_paths = re.findall(r'HREF="(/geopackages/[^"]+\.zip)"', response.text)
        if not zip_paths:
            raise RuntimeError(f"No GeoPackage archives found at {base}")
        return {f"https://sigpac-hubcloud.es{p}": ["*.gpkg"] for p in zip_paths}
