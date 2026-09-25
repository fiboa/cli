from .commons.ec import EuroCropsConverterMixin
from .nl import NLCropConverter


class NLEuroCropConverter(EuroCropsConverterMixin, NLCropConverter):
    hcat_mapping_csv = "nl_2020.csv"
    hcat_mapping_supplements = ["https://fiboa.org/code/nl/nl_2020_supplement.csv"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
