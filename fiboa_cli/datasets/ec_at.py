from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .at import Converter as ATConverter
from .commons.ec import EuroCropsV2Mixin
from .commons.hcat import AddHCATMixin


class Converter(EuroCropsV2Mixin, AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    national = ATConverter
    nuts = "at"
    years = range(2015, 2018)
