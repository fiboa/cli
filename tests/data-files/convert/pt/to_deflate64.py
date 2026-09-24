"""Recompress a fixture archive with Deflate64, as IFAP publishes 2017-2022.

python's zipfile can read and write neither, so its compressor lookup is extended with
inflate64 for the duration of the rewrite. Usage: python to_deflate64.py 2022.zip
"""

import sys
import zipfile
from unittest.mock import patch

import inflate64

ZIP_DEFLATED64 = 9


class Deflate64Compressor:
    def __init__(self):
        self._deflater = inflate64.Deflater()

    def compress(self, data):
        return self._deflater.deflate(data)

    def flush(self):
        return self._deflater.flush()


def get_compressor(compress_type, compresslevel=None):
    if compress_type == ZIP_DEFLATED64:
        return Deflate64Compressor()
    return original_get_compressor(compress_type, compresslevel)


def check_compression(compression):
    if compression != ZIP_DEFLATED64:
        original_check_compression(compression)


original_get_compressor = zipfile._get_compressor
original_check_compression = zipfile._check_compression

for path in sys.argv[1:]:
    with zipfile.ZipFile(path) as source:
        members = [(info, source.read(info)) for info in source.infolist()]
    with (
        patch.object(zipfile, "_get_compressor", get_compressor),
        patch.object(zipfile, "_check_compression", check_compression),
        zipfile.ZipFile(path, "w") as target,
    ):
        for info, data in members:
            info.compress_type = ZIP_DEFLATED64
            target.writestr(info, data)
