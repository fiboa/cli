from vecorel_cli.describe import DescribeFile
from vecorel_cli.vecorel.schemas import CollectionSchemas

from .fiboa.version import get_versions


class DescribeFiboaFile(DescribeFile):
    @staticmethod
    def get_cli_callback(cmd):
        def callback(source, num, properties, verbose):
            return DescribeFiboaFile(source).run(num=num, properties=properties, verbose=verbose)

        return callback

    def _schema_to_dict(self, schema: CollectionSchemas):
        vecorel_version, _, fiboa_version, _, extensions = get_versions(schema)

        obj = {
            "Vecorel Version": vecorel_version,
            "Fiboa Version": fiboa_version,
            "Extensions": extensions if len(extensions) > 0 else None,
        }
        return obj
