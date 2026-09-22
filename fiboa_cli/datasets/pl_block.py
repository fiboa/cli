import zipfile
from datetime import datetime

from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter

ITEMS = "https://geoportal.arimr.gov.pl/mapy/sharing/rest/content/items"
# ISO 3166-2:PL code (= TERYT voivodeship code) -> portal item of the "LPIS MKO JPO" shapefile
VOIVODESHIPS = {
    "02": "dacf163ee97149cc8e5da0f0c4435b41",  # dolnośląskie
    "04": "3cfcdbb6660245019059ab144e1cd3ac",  # kujawsko-pomorskie
    "06": "f5ec9c02e0494fba9e35dbbc0b861fa6",  # lubelskie
    "08": "a3b8ff265dff475e9050b5ff44164c8e",  # lubuskie
    "10": "f83dfac145b043268c950b7c93af0cc6",  # łódzkie
    "12": "3e8c2d1dff494e28b009494286cf4418",  # małopolskie
    "14": "659540c4407e493f82e834566beb4d1d",  # mazowieckie
    "16": "f97243dcfe6b4b1ab15e7791205e2168",  # opolskie
    "18": "caa2a7cd257f413b8897fb2b135a9cda",  # podkarpackie
    "20": "4d8e2c9ba02c449f878b2df838f857ad",  # podlaskie
    "22": "b4d1334a6b2e497a921a8045ad31b070",  # pomorskie
    "24": "1f0761da4f7b4f30b472933219cf9292",  # śląskie
    "26": "92fc87fcb4e14145a7e13f6a1717cd12",  # świętokrzyskie
    "28": "25dce1d8be1347058b2ec19c73067c2f",  # warmińsko-mazurskie
    "30": "56cc149b96714fcd8bf56905e6e7d1f2",  # wielkopolskie
    "32": "25bb8cc0d91a40a980179dbaa2366f83",  # zachodniopomorskie
}


class Converter(AdminConverterMixin, FiboaBaseConverter):
    sources = {
        f"{ITEMS}/{item}/data": f"mko_woj_{code}_akt_public.zip"
        for code, item in VOIVODESHIPS.items()
    }
    id = "pl_block"
    short_name = "Poland (blocks)"
    title = "Field blocks for Poland"
    description = """
The maximum eligible area (MKO JPO, "maksymalny kwalifikowalny obszar") of Poland's Land Parcel
Identification System, published by the paying agency ARiMR. Poland's reference parcel is the
cadastral parcel; each polygon is the part of one parcel that is eligible for the single area
payment. The layer carries no crop or land-cover class. ARiMR publishes only the current state.
    """
    provider = "Agencja Restrukturyzacji i Modernizacji Rolnictwa <https://geoportal.arimr.gov.pl/mapy/apps/sites/#/portal>"
    attribution = "© ARiMR"
    # The portal tags the data "Publiczne dane ARIMR" but states no licence
    license = "Publiczne dane ARiMR, no licence stated <https://geoportal.arimr.gov.pl/mapy/apps/sites/#/portal>"
    area_is_in_ha = False
    area_calculate_missing = True  # "0 m2" on slivers below 1 m²
    columns = {
        "geometry": "geometry",
        "id": "id",  # derived in migrate()
        "id_ewidenc": "parcel_id",
        "powierzchn": "metrics:area",
        "admin:subdivision_code": "admin:subdivision_code",  # derived in migrate()
        "determination:datetime": "determination:datetime",  # derived in file_migration()
    }
    missing_schemas = {"properties": {"parcel_id": {"type": "string"}}}

    def file_migration(self, gdf, path, uri, layer=None):
        # The data carries no date; ARiMR says to read the generation date off the zip members
        with zipfile.ZipFile(path) as archive:
            shp = next(i for i in archive.infolist() if i.filename.lower().endswith(".shp"))
        gdf["determination:datetime"] = f"{datetime(*shp.date_time):%Y-%m-%d}T00:00:00Z"
        return gdf

    def migrate(self, gdf):
        gdf["powierzchn"] = gdf["powierzchn"].str.removesuffix(" m2").astype(float)
        # A parcel's eligible area can be several patches; split first so the parts can be
        # numbered, post_migrate() then gives each part its own area
        gdf = self.split_multipart(gdf)
        gdf["id"] = gdf["id_ewidenc"].astype("string")
        part = gdf.groupby("id").cumcount()
        gdf.loc[part > 0, "id"] += "-" + (part[part > 0] + 1).astype("string")
        gdf["admin:subdivision_code"] = gdf["id_ewidenc"].str[:2]
        return super().migrate(gdf)
