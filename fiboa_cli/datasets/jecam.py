import geopandas as gpd
from vecorel_cli.vecorel.extensions import ADMIN_DIVISION

from fiboa_cli.conversion.fiboa_converter import FiboaBaseConverter
from fiboa_cli.datasets.commons.data import read_data_csv


class JecamConvert(FiboaBaseConverter):
    sources = {"https://dataverse.cirad.fr/api/access/datafile/17993": ["*.shp"]}
    id = "jecam"
    short_name = "Jecam Sirad"
    title = "Harmonized in situ JECAM datasets for agricultural land use mapping and monitoring in tropical countries"
    description = """
    Harmonized in situ JECAM datasets for agricultural land use mapping and monitoring in tropical countries

    This database contains nine land use / land cover datasets collected in a standardized manner between 2013 and 2022 in seven tropical countries within the framework of the international JECAM initiative: Burkina Faso (Koumbia), Madagascar (Antsirabe), Brazil (São Paulo and Tocantins), Senegal (Nioro, Niakhar, Mboro, Tattaguine and Koussanar), Kenya (Muranga), Cambodia (Kandal) and South Africa (Mpumalanga) (cf Study_sites‧kml).
    These quality-controlled datasets are distinguished by ground data collected at field scale by local experts, with precise geographic coordinates, and following a common protocol. This database, which contains 31879 records (24 287 crop and 7 592 non-crop) is a geographic layer in Shapefile format in a Geographic Coordinates System with Datum WGS84.
    Field surveys were conducted yearly in each study zone, either around the growing peak of the cropping season, for the sites with a main growing season linked to the rainy season such as Burkina Faso, or seasonally, for the sites with multiple cropping (e‧g. São Paulo site).
    The GPS waypoints were gathered following an opportunistic sampling approach along the roads or tracks according to their accessibility, while ensuring the best representativity of the existing cropping systems in place. GPS waypoints were also recorded on different types of non-crop classes (e‧g. natural vegetation, settlement areas, water bodies) to allow differentiating crop and non-crop classes. Waypoints were only recorded for homogenous fields/entities of at least 20 x 20 m².
    To facilitate the location of sampling areas and the remote acquisition of waypoints, field operators were equipped with GPS tablets providing access to a QGIS project with Very High Spatial Resolution (VHSR) images ordered just before the surveys. For each waypoint, a set of attributes, corresponding to the cropping practices (crop type, cropping pattern, management techniques) were recorded (for more informations about data, see data paper being published).
    These datasets can be used to validate existing cropland and crop types/practices maps in the tropics, but also, to assess the performances and the robustness of classification methods of cropland and crop types/practices in a large range of Southern farming systems.

    Citation: Jolivot, Audrey; Lebourgeois, Valentine; Ameline, Mael; Andriamanga, Valerie; Bellon, Beatriz; Castets, M
    athieu; Crespin-Boucaud, Arthur; Defourny, Pierre; Diaz, Santiana; Dieye, Mohamadou; Dupuy, Stephane; Ferraz, Rodrigo;
    Gaetano, Raffaele; Gely, Marie; Jahel, Camille; Kabore, Bertin; Lelong, Camille; Le Maire, Guerric; Leroux, Louise;
    Lo Seen, Danny; Muthoni, Martha; Ndao, Babacar; Newby, Terry; De Oliveira Santos, Cecilia Lira Melo; Rasoamalala, Eloise;
    Simoes, Margareth; Thiaw, Ibrahima; Timmermans, Alice; Tran, Annelise; Begue, Agnes, 2021,
    "Harmonized in situ JECAM datasets for agricultural land use mapping and monitoring in tropical countries",
    https://doi.org/10.18167/DVN1/P7OLAP, CIRAD Dataverse, V4
    """
    providers = [
        {
            "name": "Centre de coopération Internationale en Recherche Agronomique pour le Développement (Cirad)",
            "url": "http://www.cirad.fr",
            "roles": ["producer", "licensor"],
        }
    ]
    attribution = "JECAM SIRAD, https://doi.org/10.18167/DVN1/P7OLAP"
    license = "CC-BY-4.0"
    columns = {
        "geometry": "geometry",
        "Id": "id",
        "Area_ha": "metrics:area",
        "AcquiDate": "determination:datetime",
        "admin:country_code": "admin:country_code",
        "SiteName": "site_name",
        "CropType1": "crop:name",
        "Irrigated": "irrigated",
    }
    column_additions = {
        "crop:code_list": "https://fiboa.org/code/jecam/crop.csv",
    }
    extensions = {ADMIN_DIVISION}
    missing_schemas = {
        "properties": {
            "site_name": {"type": "string"},
            "crop:name": {"type": "string"},
            "crop:code_list": {"type": "string"},
            "irrigated": {"type": "boolean"},
        }
    }

    def migrate(self, gdf) -> gpd.GeoDataFrame:
        gdf = super().migrate(gdf)
        rows = read_data_csv("country_codes.csv")
        mapping = {row["name"]: row["alpha-2"] for row in rows}
        gdf["admin:country_code"] = gdf["Country"].map(mapping)

        gdf.loc[gdf["Area_ha"] == 0, "Area_ha"] = None
        gdf["Irrigated"] = gdf["Irrigated"].astype(bool)
        return gdf
