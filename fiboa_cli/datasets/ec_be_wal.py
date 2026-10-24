from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .be_wal import Converter as BEWALConverter
from .commons.ec import EuroCropsV2Mixin
from .commons.hcat import AddHCATMixin


class Converter(EuroCropsV2Mixin, AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    national = BEWALConverter
    nuts = "be3"
    years = [*range(2015, 2022), 2023]
