from .be_vlg import Converter as base
from .commons.ec import EuroCropsConverterMixin


class ECConverter(EuroCropsConverterMixin, base):
    sources = {
        "https://zenodo.org/records/10118572/files/BE_VLG_2021.zip?download=1": [
            "BE_VLG_2021/BE_VLG_2021_EC21.shp"
        ]
    }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.columns["BT_OMSCH"]
        del self.columns["BT_BRON"]

