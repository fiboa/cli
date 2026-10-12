from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import EuroCropsV2Mixin
from .commons.hcat import AddHCATMixin
from .es import Converter as ESConverter


class Converter(EuroCropsV2Mixin, AddHCATMixin, FiboaBaseConverter):
    national = ESConverter
    nuts = "es"
    years = range(2021, 2024)
