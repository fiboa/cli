from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import EuroCropsConverterMixin, ec_url


class Convert(EuroCropsConverterMixin, FiboaBaseConverter):
    # See https://data.europa.eu/data/datasets/092425a1-90c6-4461-b1a6-6f5b0f72748f?locale=ro
    ec_mapping_csv = "ro_no_year.csv"
    sources = {"https://zenodo.org/records/14094196/files/RO_ny.zip?download=1": ["RO/*.shp"]}
    id = "ec_ro"
    short_name = "Romania"
    title = "Field boundaries for Romania"
    description = """
        The dataset includes the land cover layer from the Romanian side of the Romania-Bulgaria cross-border area (Mehedinți, Dolj, Olt, Teleorman, Giurgiu, Călărași, Constanța counties), developed within the project "Common strategy for territorial development of the cross-border area Romania-Bulgaria", code MIS-ETC 171, funded by the Romania-Bulgaria Cross-Border Cooperation Programme 2007-2013.

        The dataset is published in the WGS 84 / UTM zone 35N coordinate system (to be compatible with the similar dataset on the Bulgarian side).

        The dataset is in line with the conceptual framework described in the Land Cover Data Specifications for the Implementation of the INSPIRE Directive (version 3.0). The information layer was developed based on a methodology developed within the project, which was carried out as follows: - analysis and harmonisation of the land cover classification system; - acquisition and processing of the reference data, listed below; - verification and validation of the quality of the spatial data produced;
    """
    providers = [
        {
            "name": "Ministry of Regional Development and Public Administration",
            "url": "http://spatial.mdrap.ro",
            "roles": ["producer", "licensor"],
        }
    ]
    license = "CC-0"
    column_additions = {
        "determination:datetime": "2017-01-01T00:00:00Z",
        "crop:code_list": ec_url("ro_no_year.csv"),
    }
    index_as_id = True
    columns = {
        "id": "id",
        "geometry": "geometry",
        "AREA_HA": "metrics:area",
        "SOURCE": "source",
        "LC_MAPCODE": "crop:code",
        "LC_CLASS_N": "crop:name",
    }
    column_migrations = {
        "AREA_HA": lambda x: x / 10000,
    }
    missing_schemas = {"properties": {"source": {"type": "string"}}}
    column_filters = {
        # Fields
        # A=Arable Land, CAG=Covered Agricultural Land, N+G=Grassland, P=Trees, R=Rice, T=Trees
        "LC_MAPCODE": lambda col: col.isin(["A", "CAG", "G", "N", "P", "R", "T"])
    }
    extensions = {"https://fiboa.github.io/crop-extension/v0.2.0/schema.yaml"}
