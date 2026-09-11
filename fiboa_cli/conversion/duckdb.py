from vecorel_cli.conversion.duckdb import DuckDBBaseConverter

from .fiboa_converter import FiboaBaseConverter


# This converter is experimental, use with caution.
# Results may not be fully fiboa compliant yet.
# Use this primarily for datasets that are too large to be processed by the default converter
class FiboaDuckDBBaseConverter(DuckDBBaseConverter, FiboaBaseConverter):
    pass
