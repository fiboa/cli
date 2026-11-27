from vecorel_cli.conversion.admin import AdminConverterMixin

from ..conversion.fiboa_converter import FiboaBaseConverter
from .commons.ec import EuroCropsV2Mixin
from .commons.hcat import AddHCATMixin
from .de_bb import Converter as DEBBConverter


class Converter(EuroCropsV2Mixin, AdminConverterMixin, AddHCATMixin, FiboaBaseConverter):
    national = DEBBConverter
    nuts = "de4"
    years = range(2010, 2024)
    # landscape elements (hedges, tree rows, copses, wetlands, single trees, stone walls, rock
    # ridges) mapped as their own polygons from 2018
    drop_codes = {"1", "2", "3", "4", "5", "10011", "10012"}
