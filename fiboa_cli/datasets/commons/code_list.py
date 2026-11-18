from typing import Optional

from .data import read_data_csv
from .hcat import CROP_EXTENSION


class CodeListMixin:
    """
    Names the crop codes from a code list with the columns original_code, original_name and
    name_en, and publishes that list as crop:code_list.

    The list is bundled in data-files (code_list_file) and hosted at code_list. Codes match
    regardless of case, and crop:code takes the list's spelling, so every published code is
    in its own crop:code_list.
    """

    code_list: Optional[str] = None
    code_list_file: Optional[str] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rebind instead of mutating: the class-level dicts are shared with AdminConverterMixin,
        # and a converter's own `extensions` would otherwise replace the crop extension.
        self.extensions = set(self.extensions) | {CROP_EXTENSION}
        self.columns = {
            **self.columns,
            "crop:name": "crop:name",
            "crop:name_en": "crop:name_en",
            "crop:code_list": "crop:code_list",
        }

    def post_migrate(self, gdf):
        gdf = super().post_migrate(gdf)
        # Columns are still source-named at this point
        attribute = self._source_column("crop:code", self.get_columns(gdf))
        if attribute is None:
            return gdf
        rows = {r["original_code"].strip().upper(): r for r in read_data_csv(self.code_list_file)}
        key = gdf[attribute].astype("string").str.strip().str.upper()

        def lookup(field):
            return key.map({k: r[field] for k, r in rows.items()}).astype("string")

        gdf[attribute] = lookup("original_code").fillna(gdf[attribute].astype("string"))
        gdf["crop:name"] = lookup("original_name")
        gdf["crop:name_en"] = lookup("name_en")
        gdf["crop:code_list"] = self.code_list
        return gdf
