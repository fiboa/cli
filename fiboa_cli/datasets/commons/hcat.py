import csv
from io import StringIO
from typing import Optional

import geopandas as gpd
from vecorel_cli.vecorel.util import load_file

HCAT_EXTENSION = "https://fiboa.org/hcat-extension/v0.3.0/schema.yaml"
CROP_EXTENSION = "https://fiboa.org/crop-extension/v0.2.0/schema.yaml"


class AddHCATMixin:
    """
    Adds HCAT columns to a GeoDataFrame, based on the crop-extension crop:code column and a specified csv-mapping
    Automatically adds crop:code_list to the columns, and adds HCAT and CROP extensions.
    """

    ec_mapping_csv: Optional[str] = None  # TODO rename to hcat_mapping_csv
    mapping_file = None
    ec_mapping: Optional[dict] = None  # TODO rename to hcat_mapping

    hcat_columns = {
        "hcat:name_en": "hcat:name_en",
        "hcat:name": "hcat:name",
        "hcat:code": "hcat:code",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.columns |= self.hcat_columns | {"crop:code_list": "crop:code_list"}
        self.extensions = getattr(self, "extensions", set()) | {CROP_EXTENSION, HCAT_EXTENSION}

    def convert(self, *args, **kwargs):
        self.mapping_file = kwargs.get("mapping_file")
        if not self.mapping_file:
            assert self.ec_mapping_csv is not None, (
                "Specify ec_mapping_csv in Converter, e.g. find them at https://github.com/maja601/EuroCrops/tree/main/csvs/country_mappings"
            )
        return super().convert(*args, **kwargs)

    def get_code_column(self, gdf):
        try:
            attribute = next(k for k, v in self.columns.items() if v == "crop:code")
        except StopIteration:
            raise Exception(f"Misssing crop:code column in converter {self.__class__.__name__}")
        col = gdf[attribute]
        # Should be corrected in original parser
        return col if col.dtype == "object" else col.astype(str)

    def add_hcat(self, gdf):
        # Lookup column that will be renamed after the migration to hcat:code
        hcat_code_column = next(k for k, v in self.hcat_columns.items() if v == "hcat:code")
        if hcat_code_column not in gdf.columns:
            # Add HCAT columns based on crop-columns
            # Map to HCAT categories by using the mapping from the csv file

            if self.ec_mapping is None:
                self.ec_mapping = load_ec_mapping(self.ec_mapping_csv, url=self.mapping_file)
            crop_code_col = self.get_code_column(gdf)

            def map_to(attribute):
                return {e["original_code"]: e[attribute] for e in self.ec_mapping}

            for k, v in zip(
                self.hcat_columns.keys(), ("translated_name", "HCAT3_name", "HCAT3_code")
            ):
                gdf[k] = crop_code_col.map(map_to(v))

        if "crop:code_list" not in gdf.columns:
            gdf["crop:code_list"] = (
                ec_url(self.ec_mapping_csv) if self.ec_mapping_csv else self.mapping_file
            )
        return gdf

    def migrate(self, gdf) -> gpd.GeoDataFrame:
        gdf = super().migrate(gdf)
        return self.add_hcat(gdf)


def ec_url(csv_file):
    return f"https://raw.githubusercontent.com/maja601/EuroCrops/refs/heads/main/csvs/country_mappings/{csv_file}"


def load_ec_mapping(csv_file=None, url=None):
    if not (csv_file or url):
        raise ValueError("Either csv_file or url must be specified")
    if not url:
        url = ec_url(csv_file)
    content = load_file(url)
    return list(csv.DictReader(StringIO(content.decode("utf-8"))))
