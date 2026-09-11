import csv
from io import StringIO
from typing import Optional

import geopandas as gpd
import numpy as np
import pandas as pd
from vecorel_cli.vecorel.util import load_file

HCAT_EXTENSION = "https://fiboa.org/hcat-extension/v0.3.0/schema.yaml"
CROP_EXTENSION = "https://fiboa.org/crop-extension/v0.2.0/schema.yaml"


class AddHCATMixin:
    """
    Adds HCAT columns to a GeoDataFrame, based on the crop-extension crop:code column and a specified csv-mapping
    Automatically adds crop:code_list to the columns, and adds HCAT and CROP extensions.
    """

    ec_mapping_csv: Optional[str] = None  # TODO rename to hcat_mapping_csv
    # Tables that fill gaps in the main one. EuroCrops splits some countries in
    # two — fr_2018.csv holds the code list of that campaign and
    # fr_other_years.csv the codes that appeared later — and a converter that
    # names only the first leaves every later code unmapped. Rows here win over
    # the main table where both carry a code.
    ec_mapping_supplements: list[str] = []
    # Match on the crop name where the table has no row for the code. EuroCrops
    # keys most tables on the code, but be_wal_all_years.csv leaves
    # original_code empty in 208 of its 298 rows and names the crop instead, so
    # matching on the code alone loses every crop whose coded row is missing.
    ec_mapping_name_fallback = False
    mapping_file = None
    ec_mapping: Optional[list[dict]] = None  # TODO rename to hcat_mapping

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
            assert isinstance(self.ec_mapping_csv, str), (
                "Specify proper ec_mapping_csv in Converter, e.g. find them at https://github.com/maja601/EuroCrops/tree/main/csvs/country_mappings"
            )
        return super().convert(*args, **kwargs)

    def get_code_column(self, gdf, code="crop:code"):
        try:
            attribute = next(k for k, v in self.columns.items() if v == code)
        except StopIteration:
            raise Exception(f"Misssing {code} column in converter {self.__class__.__name__}")
        col = gdf[attribute]
        # Should be corrected in original parser
        return col if col.dtype == "object" else col.astype(str)

    def add_hcat(self, gdf):
        # Lookup column that will be renamed after the migration to hcat:code
        hcat_code_column = next(k for k, v in self.hcat_columns.items() if v == "hcat:code")
        if hcat_code_column not in gdf.columns:
            code_sources = [k for k, v in self.columns.items() if v in ("crop:code", "crop:name")]
            if not any(k in gdf.columns for k in code_sources):
                # this edition carries no crop columns at all: nothing to map
                return gdf
            # Add HCAT columns based on crop-columns
            # Map to HCAT categories by using the mapping from the csv file

            if self.ec_mapping is None:
                self.ec_mapping = load_ec_mapping(self.ec_mapping_csv, url=self.mapping_file)
                for supplement in self.ec_mapping_supplements:
                    self.ec_mapping = self.ec_mapping + load_ec_mapping(supplement)

            from_code = "original_code"
            if from_code not in self.ec_mapping[0]:
                # Some code lists have no code, only a crop_name
                from_code = "original_name"
                crop_code_col = self.get_code_column(gdf, "crop:name")
            else:
                crop_code_col = self.get_code_column(gdf)

            def map_to(attribute):
                return {e[from_code]: e[attribute] or None for e in self.ec_mapping}

            name_col = None
            if self.ec_mapping_name_fallback and from_code == "original_code":
                name_col = self.get_code_column(gdf, "crop:name")

            def map_by_name(attribute):
                # Three Walloon crops are spelled with a trailing space in the
                # table ("Luzerne lupuline "), so both sides are stripped.
                return {
                    (e["original_name"] or "").strip(): e[attribute] or None
                    for e in self.ec_mapping
                    if not (e["original_code"] or "").strip()
                }

            col = None
            for k, v in zip(
                self.hcat_columns.keys(), ("translated_name", "HCAT3_name", "HCAT3_code")
            ):
                if v in self.ec_mapping[0]:
                    col = crop_code_col.map(map_to(v))
                    if name_col is not None:
                        col = col.fillna(name_col.str.strip().map(map_by_name(v)))
                    gdf[k] = col
                    assert np.unique(col[~col.isna()]).size > 0, "No HCAT crops mapped"

            if col is not None and col.isna().any():
                index = [
                    k for k, v in self.columns.items() if v.startswith("crop:") and k in gdf.columns
                ]
                missing = gdf[col.isna()][index].drop_duplicates()
                missing.reset_index(drop=True, inplace=True)
                with pd.option_context(
                    "display.max_colwidth",
                    None,
                    "display.max_columns",
                    None,
                    "display.max_rows",
                    None,
                ):
                    self.info(f"Missing codes in HCAT mapping:\n{missing}")

        if "crop:code_list" not in gdf.columns:
            gdf["crop:code_list"] = (
                ec_url(self.ec_mapping_csv) if self.ec_mapping_csv else self.mapping_file
            )
        return gdf

    def post_migrate(self, gdf) -> gpd.GeoDataFrame:
        gdf = super().post_migrate(gdf)
        return self.add_hcat(gdf)


def ec_url(csv_file):
    if csv_file.startswith("https://"):
        return csv_file
    return f"https://raw.githubusercontent.com/maja601/EuroCrops/refs/heads/main/csvs/country_mappings/{csv_file}"


def load_ec_mapping(csv_file=None, url=None):
    if not (csv_file or url):
        raise ValueError("Either csv_file or url must be specified")
    if not url:
        url = ec_url(csv_file)
    content = load_file(url)
    return list(csv.DictReader(StringIO(content.decode("utf-8"))))
