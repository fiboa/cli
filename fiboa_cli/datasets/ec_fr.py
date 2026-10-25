from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import EuroCropsV2Mixin
from .commons.hcat import AddHCATMixin
from .fr import FRConverter


class Converter(EuroCropsV2Mixin, AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    national = FRConverter
    nuts = "fr"
    # IGN's RPG downloads run 2017 and 2019 onwards
    years = (2015, 2016, 2018)
