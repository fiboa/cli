from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import EuroCropsV2Mixin
from .commons.hcat import AddHCATMixin
from .ee import Convert as EEConverter


class Converter(EuroCropsV2Mixin, AddHCATMixin, FiboaBaseConverter):
    national = EEConverter
    nuts = "ee"
    # PRIA's WFS layers before 2016 are empty
    years = (2015,)
    code_from_name = True
