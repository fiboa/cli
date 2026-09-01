import pandas as pd
from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter

URL = (
    "https://service.gdi-sh.de/SH_OpenGBD/feeds/Atom_SH_Feldblockfinder_OpenGBD/data/"
    "Feldbloecke_{year}_GPKG.zip"
)


def parse_date(col):
    # Every edition writes fachguelti as DD.MM.YYYY, which is not an ISO date:
    # left as text it reaches the STAC step as "Invalid isoformat string".
    return pd.to_datetime(col, format="%d.%m.%Y")


def parse_decimal(col):
    # 2023, 2025 and 2026 write the area as text with a decimal comma; in 2024
    # it is a Real and needs no conversion.
    if pd.api.types.is_numeric_dtype(col):
        return col
    return pd.to_numeric(col.str.replace(",", ".", regex=False))


class Converter(AdminConverterMixin, FiboaBaseConverter):
    # Name the GeoPackage inside the archive rather than handing GDAL the
    # archive itself: the 2023 GeoPackage was written with user_version = 0, so
    # the GPKG driver identifies it by the .gpkg extension alone and
    # "/vsizip/Feldbloecke_2023_GPKG.zip" matches no driver at all. The member
    # is named differently in every edition (Feldbloecke_2023.gpkg, FB_2024.gpkg,
    # FB_20250101.gpkg, FB_20260101.gpkg), hence the glob.
    variants = {
        str(year): {URL.format(year=year): ["*.gpkg"]} for year in range(2026, 2023 - 1, -1)
    }
    id = "de_sh"
    admin_subdivision_code = "SH"
    short_name = "Germany, Schleswig-Holstein"
    title = "Field boundaries for Schleswig-Holstein (SH), Germany"
    description = """A field block (German: "Feldblock") is a contiguous agricultural area surrounded by permanent boundaries, which is cultivated by one or more farmers with one or more crops, is fully or partially set aside or is fully or partially taken out of production."""
    provider = "Land Schleswig-Holstein <https://sh-mis.gdi-sh.de/catalog/#/datasets/iso/21f67269-780f-4f3c-8f66-03dde27acfe7>"
    license = "DL-DE-ZERO-2.0"
    extensions = {"https://fiboa.org/flik-extension/v0.2.0/schema.yaml"}

    # The source spellings drift between editions: 2023 has its own set of
    # names, 2024 is mixed case, 2025 and 2026 are upper case. Without this the
    # upper-case editions silently lose determination:datetime and metrics:area
    # ("Column 'fachguelti' not found in dataset, removing from schema").
    COLUMN_RENAMES = {
        # 2025, 2026
        "FACHGUELTI": "fachguelti",
        "FLAECHE": "Flaeche",
        # 2023; flgesamt (gross) equals flnetto (net) in all 198,614 rows
        "flident": "FLIK",
        "flgesamt": "Flaeche",
        "hbn": "HBN",
    }

    def migrate(self, gdf):
        renames = {old: new for old, new in self.COLUMN_RENAMES.items() if old in gdf.columns}
        if renames:
            gdf = gdf.rename(columns=renames)
        return super().migrate(gdf)

    columns = {
        "geometry": "geometry",
        "fachguelti": "determination:datetime",
        "FLIK": ("flik", "id"),
        "Flaeche": "metrics:area",
        "HBN": "hbn",
    }
    column_migrations = {
        "fachguelti": parse_date,
        "Flaeche": parse_decimal,
    }
    missing_schemas = {"properties": {"hbn": {"type": "string"}}}
