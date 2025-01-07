from .nl_crop import NLCropConverter
from .commons.ec import EuroCropsConverterMixin


class NLEuroCropConverter(EuroCropsConverterMixin, NLCropConverter):
    ec_mapping_csv = "nl_2020.csv"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
