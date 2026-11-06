import pandas as pd
from vecorel_cli.vecorel.extensions import ADMIN_DIVISION

from ..conversion.fiboa_converter import FiboaBaseConverter

RECORD = "https://zenodo.org/api/records/10479122/files"
SOURCE = {
    f"{RECORD}/GloCAB_Field_Boundaries.zip/content": [
        "GloCAB_Field_Boundaries/GloCAB_field_boundaries.shp"
    ]
}

# Table A of GloCAB_Field_Boundary_ReadMe.pdf: the mapping date of each region
MAPPING_DATES = {
    "Brazil_A": "2019-08",
    "Brazil_B": "2019-07",
    "Canada_A": "2018-05",
    "Russia_A": "2019-07",
    "Russia_B": "2019-08",
    "Russia_C": "2019-04",
    "Russia_D": "2019-04",
    "Russia_E": "2018-10",
    "Ukraine_A": "2017-03",
    "Ukraine_B": "2017-03",
    "Ukraine_C": "2017-07",
    "Ukraine_D": "2016-08",
    "Ukraine_E": "2017-07",
    "Ukraine_F": "2017-06",
    "Ukraine_G": "2017-06",
    "Ukraine_H": "2020-07",
    "USA_A": "2018-11",
    "USA_B": "2019-10",
    "USA_C": "2018-04",
    "USA_D": "2020-09",
    "USA_E": "2017-09",
    "USA_F": "2017-09",
}
COUNTRIES = {"Brazil": "BR", "Canada": "CA", "Russia": "RU", "Ukraine": "UA", "USA": "US"}


class Converter(FiboaBaseConverter):
    sources = SOURCE

    id = "glocab"
    short_name = "GloCAB"
    title = "GloCAB cropland field boundaries (Brazil, Canada, Russia, Ukraine, USA)"
    description = """
190,832 cropland field boundaries in 22 regions of Brazil, Canada, Russia, Ukraine and the United
States, digitised by hand over 20 m Sentinel-2 imagery by geospatial analysts at the University of
Maryland and quality-checked by a senior team member, as a by-product of the Global Cropland Area
Burned (GloCAB) product. The readme gives each region a mapping date (a month, Table A), which is
each field's determination date here (2016 to 2020, by region).
Where fields were too small to identify, the analyst digitised a larger boundary around several
fields and set the `no_area` flag: those polygons are not true field boundaries.
`predominant_crop` is the predominant crop type of the region, not of the field.
    """
    provider = "University of Maryland <https://doi.org/10.5281/zenodo.10479122>"
    attribution = (
        "Hall, J. V., Argueta, F., Giglio, L.: GloCAB Cropland Field Boundary Dataset, "
        "Zenodo, doi:10.5281/zenodo.10479122"
    )
    license = "CC-BY-4.0"

    extensions = {ADMIN_DIVISION}
    columns = {
        "geometry": "geometry",
        "id": "id",
        # Area_km2 is not mapped: in USA_C every value is ~2.19x the polygon's area (a Web
        # Mercator measurement) and 187 Ukraine_D values disagree with their polygons, so
        # metrics:area is measured from the geometry instead.
        "determination:datetime": "determination:datetime",
        "admin:country_code": "admin:country_code",
        "Ctry_Reg": "region",
        "No_Area": "no_area",
        "CropType": "predominant_crop",
    }
    column_migrations = {"No_Area": lambda col: col.astype(bool)}
    missing_schemas = {
        "properties": {
            "region": {
                "type": "string",
                "description": "The GloCAB region (Country ID in the readme)",
            },
            "no_area": {
                "type": "boolean",
                "description": "The polygon encloses several fields too small to identify; "
                "it is not a true field boundary",
            },
            "predominant_crop": {
                "type": "string",
                "description": "The predominant crop type of the region, not of the field",
            },
        }
    }

    def file_migration(self, gdf, path, uri, layer=None):
        # The source has no identifier; the row number in the shapefile is stable
        gdf["id"] = [f"{region}-{i}" for i, region in enumerate(gdf["Ctry_Reg"])]
        dates = gdf["Ctry_Reg"].map(MAPPING_DATES)
        unknown = sorted(set(gdf.loc[dates.isna(), "Ctry_Reg"]))
        if unknown:
            raise ValueError(f"Regions without a mapping date: {unknown}")
        gdf["determination:datetime"] = pd.to_datetime(dates + "-01", utc=True)
        gdf["admin:country_code"] = gdf["Ctry_Reg"].str.split("_").str[0].map(COUNTRIES)
        return super().file_migration(gdf, path, uri, layer)
