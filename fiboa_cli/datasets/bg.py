from vecorel_cli.conversion.admin import AdminConverterMixin

from fiboa_cli.conversion.fiboa_converter import FiboaBaseConverter

# The ministry's GeoServer names the campaign in the layer, not in a parameter,
# and publishes Agricultural_Land_<year> for 2021 onwards. Its Physical_Blocks
# layers cover the same blocks including forest, urban and roads (1.5M of them
# in 2025, against 226,592 agricultural); this is the agricultural subset.
BASE = (
    "http://inspire.mzh.government.bg:8080/geoserver/ows?request=GetFeature&service=WFS"
    "&version=2.0.0&outputFormat=SHAPE-ZIP&typeNames=VectorData:Agricultural_Land_{year}"
    # without this the Bulgarian names come back as ISO-8859-1 question marks
    "&format_options=CHARSET:UTF-8"
)


class BGConverter(AdminConverterMixin, FiboaBaseConverter):
    # the response carries no file name of its own
    variants = {
        str(year): {BASE.format(year=year): f"bg_agricultural_land_{year}.zip"}
        for year in range(2025, 2020, -1)
    }

    id = "bg"
    short_name = "Bulgaria"
    title = "Field blocks for Bulgaria"
    license = "CC-BY-4.0"
    provider = "Ministry of Agriculture and Food <https://www.mzh.government.bg>"
    description = """
The agricultural part of the Bulgarian physical block register (физически блокове): a physical block is a
contiguous area of land bounded by permanent features, identified as <EKATTE settlement code>-<block number>
and classified by its use. The register has been produced from field checks and orthophoto mapping.

These layers hold the blocks used agriculturally — arable land, greenhouses, rice fields and courtyards —
where the Physical_Blocks layers of the same service also carry forest, urban and transport land.
    """
    # The layer carries no area column; the blocks are in UTM 35N metres.
    area_calculate_missing = True
    # PHBIDENT identifies the block, and a block is listed once per usage — and
    # sometimes twice for the same usage (42 blocks of the 226,592 in 2025, 40
    # of them with the same code), so the row position identifies the polygon.
    index_as_id = True
    columns = {
        "geometry": "geometry",
        "id": "id",
        "PHBIDENT": "block_id",
        "USAGECODE": "crop:code",
        "USAGEBUL": "crop:name",
        "USAGEENG": "crop:name_en",
        # only 2021 and 2022 publish an area; the rest is measured from the
        # geometry, which is in UTM 35N metres
        "AREA": "metrics:area",
    }
    extensions = {"https://fiboa.org/crop-extension/v0.2.0/schema.yaml"}
    missing_schemas = {"properties": {"block_id": {"type": "string"}}}

    # 2021 and 2022 are a different release: the block and its usage are one
    # field, ELGIDENT = <settlement>-<block>-<usage>, where 2023 onwards name
    # the block in PHBIDENT and the usage in USAGECODE. 2021 truncates the
    # Bulgarian name to ten characters and 2022 drops it altogether.
    def migrate(self, gdf):
        if "ELGIDENT" in gdf.columns:
            parts = gdf["ELGIDENT"].str.rsplit("-", n=1)
            gdf["PHBIDENT"] = parts.str[0]
            gdf["USAGECODE"] = parts.str[-1].str.zfill(3)
        if "AREA1" in gdf.columns:
            gdf = gdf.rename(columns={"AREA1": "AREA"})
        return super().migrate(gdf)

    # GeoServer writes the charset into a .cst file, which GDAL does not read (it
    # looks for .cpg), so the Bulgarian names arrive as Latin-1 mojibake.
    def read_data(self, paths, **kwargs):
        kwargs.setdefault("encoding", "UTF-8")
        return super().read_data(paths, **kwargs)
