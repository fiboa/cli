from fiboa_cli.datasets.commons.hcat import AddHCATMixin, ec_url, load_ec_mapping  # noqa: F401


class EuroCropsConverterMixin(AddHCATMixin):
    """
    Adds HCAT columns to a GeoDataFrame, useful for transforming datasets supplied by the Eurocrops project.
    The Eurocrops files have their own column names, so we need to map them to HCAT extension names.
    Also modifies the dataset title and provider to reflect the source.
    """

    ec_year = None
    hcat_columns = {
        "EC_trans_n": "hcat:name_en",
        "EC_hcat_n": "hcat:name",
        "EC_hcat_c": "hcat:code",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.id.startswith("ec_"):
            self.id = "ec_" + self.id
        suffix = " - Eurocrops"
        if self.ec_year is not None:
            suffix = f"{suffix} {self.ec_year}"

        self.title += suffix
        self.short_name += suffix

        provider = "EuroCrops <https://github.com/maja601/EuroCrops>"
        self.provider = (f"{self.provider}, {provider}") if self.provider else provider
        self.license = "CC-BY-SA-4.0"
