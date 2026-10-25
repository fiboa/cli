from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .be_vlg import Converter as BEVLGConverter
from .commons.ec import EuroCropsV2Mixin
from .commons.hcat import AddHCATMixin


class Converter(EuroCropsV2Mixin, AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    national = BEVLGConverter
    nuts = "be2"
    years = range(2008, 2018)
    # buildings: "Hoofdgebouwen", "Andere gebouwen"
    drop_codes = {"1", "2"}
