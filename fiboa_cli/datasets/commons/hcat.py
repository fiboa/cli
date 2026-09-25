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

    # CSV that maps the source crop codes to HCAT: a URL, or a file name in the
    # EuroCrops country_mappings folder (see hcat_mapping_url)
    hcat_mapping_csv: Optional[str] = None
    # Tables that fill gaps in the main one, for a country whose main table does
    # not carry every code the source uses. Rows here win where both carry a code.
    hcat_mapping_supplements: list[str] = []
    # The column the supplements are keyed on when the source already carries HCAT
    hcat_supplement_key = "crop:code"
    # Match on the crop name where the table has no row for the code:
    # be_wal_all_years.csv leaves original_code empty in 208 of its 298 rows.
    hcat_mapping_name_fallback = False
    mapping_file = None
    hcat_mapping: Optional[list[dict]] = None

    # Variants whose source has no crop columns at all; they convert without the
    # crop/HCAT extensions. Only variants listed here take that path, so a crop
    # column missing anywhere else still fails loudly.
    variants_without_crops: set[str] = set()

    hcat_columns = {
        "hcat:name_en": "hcat:name_en",
        "hcat:name": "hcat:name",
        "hcat:code": "hcat:code",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.columns |= self.hcat_columns | {"crop:code_list": "crop:code_list"}
        self.extensions = getattr(self, "extensions", set()) | {CROP_EXTENSION, HCAT_EXTENSION}

    def has_no_crops(self) -> bool:
        """Whether the selected variant has no crop columns; override when no edition has any."""
        return self.variant in self.variants_without_crops

    def select_variant(self, variant):
        # __init__ ran before the variant was known, so align the extensions and
        # columns with the chosen variant (in both directions)
        super().select_variant(variant)
        crop_entries = self.hcat_columns | {"crop:code_list": "crop:code_list"}
        if self.has_no_crops():
            self.extensions -= {CROP_EXTENSION, HCAT_EXTENSION}
            removed = set(crop_entries.values())
            self.columns = {k: v for k, v in self.columns.items() if v not in removed}
        else:
            self.extensions |= {CROP_EXTENSION, HCAT_EXTENSION}
            self.columns |= crop_entries

    def convert(self, *args, **kwargs):
        self.mapping_file = kwargs.get("mapping_file")
        if not self.mapping_file:
            assert self.hcat_mapping_csv is not None, (
                "Specify hcat_mapping_csv in Converter: a URL to an HCAT mapping CSV or a file name from https://github.com/maja601/EuroCrops/tree/main/csvs/country_mappings"
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
        if self.has_no_crops():
            return gdf

        # Lookup column that will be renamed after the migration to hcat:code
        hcat_code_column = next(k for k, v in self.hcat_columns.items() if v == "hcat:code")
        if hcat_code_column in gdf.columns:
            gdf = self.correct_resolved_hcat(gdf)
        else:
            # Add HCAT columns based on crop-columns
            # Map to HCAT categories by using the mapping from the csv file

            if self.hcat_mapping is None:
                self.hcat_mapping = load_hcat_mapping(self.hcat_mapping_csv, url=self.mapping_file)
                for supplement in self.hcat_mapping_supplements:
                    self.hcat_mapping = self.hcat_mapping + load_hcat_mapping(supplement)

            from_code = "original_code"
            if from_code not in self.hcat_mapping[0]:
                # Some code lists have no code, only a crop_name
                from_code = "original_name"
                crop_code_col = self.get_code_column(gdf, "crop:name")
            else:
                crop_code_col = self.get_code_column(gdf)

            def map_to(attribute):
                return {e[from_code]: e[attribute] or None for e in self.hcat_mapping}

            name_col = None
            if self.hcat_mapping_name_fallback and from_code == "original_code":
                name_col = self.get_code_column(gdf, "crop:name")

            def map_by_name(attribute):
                # Three Walloon crops carry a trailing space in the table.
                return {
                    (e["original_name"] or "").strip(): e[attribute] or None
                    for e in self.hcat_mapping
                    if not (e["original_code"] or "").strip()
                }

            col = None
            for k, v in zip(
                self.hcat_columns.keys(), ("translated_name", "HCAT3_name", "HCAT3_code")
            ):
                if v in self.hcat_mapping[0]:
                    col = crop_code_col.map(map_to(v))
                    if name_col is not None:
                        col = col.fillna(name_col.str.strip().map(map_by_name(v)))
                    gdf[k] = col
                    assert np.unique(col[~col.isna()]).size > 1, "No HCAT crops mapped"

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
                hcat_mapping_url(self.hcat_mapping_csv)
                if self.hcat_mapping_csv
                else self.mapping_file
            )
        return gdf

    def correct_resolved_hcat(self, gdf):
        """The source carries HCAT already (EuroCrops); the supplements still win for their codes."""
        rows = [row for url in self.hcat_mapping_supplements for row in load_hcat_mapping(url)]
        if not rows:
            return gdf
        key = self.get_code_column(gdf, self.hcat_supplement_key).str.strip()
        for column, attribute in zip(
            self.hcat_columns.keys(), ("translated_name", "HCAT3_name", "HCAT3_code")
        ):
            fix = {row["original_code"].strip(): row[attribute] for row in rows}
            hit = key.isin(fix.keys())
            if column in gdf.columns and hit.any():
                gdf.loc[hit, column] = key[hit].map(fix)
        return gdf

    def post_migrate(self, gdf) -> gpd.GeoDataFrame:
        gdf = super().post_migrate(gdf)
        return self.add_hcat(gdf)


def hcat_mapping_url(csv_file):
    """Returns URLs as-is and resolves bare file names to the EuroCrops country_mappings folder."""
    if "://" in csv_file:
        return csv_file
    return f"https://raw.githubusercontent.com/maja601/EuroCrops/refs/heads/main/csvs/country_mappings/{csv_file}"


def load_hcat_mapping(csv_file=None, url=None):
    if not (csv_file or url):
        raise ValueError("Either csv_file or url must be specified")
    if not url:
        url = hcat_mapping_url(csv_file)
    content = load_file(url)
    return list(csv.DictReader(StringIO(content.decode("utf-8"))))
