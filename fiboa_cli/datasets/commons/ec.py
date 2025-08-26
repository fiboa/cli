import csv
from io import StringIO

import geopandas as gpd
from vecorel_cli.vecorel.util import load_file


class EuroCropsConverterMixin:
    license = "CC-BY-SA-4.0"

    ec_mapping_csv = None
    mapping_file = None
    ec_mapping = None
    ec_year = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.id.startswith("ec_"):
            self.id = "ec_" + self.id

        suffix = " - Eurocrops"
        if self.ec_year is not None:
            suffix = f"{suffix} {self.ec_year}"

        self.title += suffix
        self.short_name += suffix

        self.description = (
            self.description.strip()
            + """

    This dataset is an extended version of the original dataset, with additional columns and attributes added by the EuroCrops project.

    The project developed a new **Hierarchical Crop and Agriculture Taxonomy (HCAT)** that harmonises all declared crops across the European Union.
    In the data you'll find this as additional attributes:

    - `EC_trans_n`: The original crop name translated into English
    - `EC_hcat_n`: The machine-readable HCAT name of the crop
    - `EC_hcat_c`: The 10-digit HCAT code indicating the hierarchy of the crop
        """
        )

        self.providers += [
            {
                "name": "EuroCrops",
                "url": "https://github.com/maja601/EuroCrops",
                "roles": ["processor"],
            }
        ]

        self.extensions = getattr(self, "extensions", set())
        self.extensions.add("https://fiboa.github.io/hcat-extension/v0.2.0/schema.yaml")
        self.columns |= {
            "EC_trans_n": "ec:translated_name",
            "EC_hcat_n": "ec:hcat_name",
            "EC_hcat_c": "ec:hcat_code",
        }
        self.license = "CC-BY-SA-4.0"

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
        if self.ec_mapping is None:
            self.ec_mapping = load_ec_mapping(self.ec_mapping_csv, url=self.mapping_file)
        crop_code_col = self.get_code_column(gdf)

        def map_to(attribute):
            return {e["original_code"]: e[attribute] for e in self.ec_mapping}

        gdf["EC_trans_n"] = crop_code_col.map(map_to("translated_name"))
        gdf["EC_hcat_n"] = crop_code_col.map(map_to("HCAT3_name"))
        gdf["EC_hcat_c"] = crop_code_col.map(map_to("HCAT3_code"))
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
