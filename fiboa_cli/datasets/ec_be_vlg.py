from .be_vlg import Converter as BEVLGBaseConverter
from .commons.ec import EuroCropsConverterMixin


class ECConverter(EuroCropsConverterMixin, BEVLGBaseConverter):
    id = "ec_be_vlg"
    sources = {
        "https://zenodo.org/records/10118572/files/BE_VLG_2021.zip?download=1": [
            "BE_VLG_2021/BE_VLG_2021_EC21.shp"
        ]
    }
    # This is the single 2021 EuroCrops release, not the yearly agpa downloads
    # the Flemish parent declares; say so rather than leaning on `sources`
    # taking precedence over inherited variants.
    variants = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.columns["BT_OMSCH"]
