from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import EuroCropsV2Mixin
from .commons.hcat import AddHCATMixin
from .de_nrw import Converter as DENRWConverter


class Converter(EuroCropsV2Mixin, AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    national = DENRWConverter
    nuts = "dea"
    years = range(2019, 2024)
