from semantic_version import SimpleSpec

__version__ = "0.10.0"
fiboa_version = "0.3.0"
supported_fiboa_versions = ">=0.3.0,<0.4.0"


def is_supported(version):
    supported = SimpleSpec(supported_fiboa_versions)
    return supported.match(version)
