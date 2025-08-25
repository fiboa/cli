from vecorel_cli.registry import Registry

from .registry import FiboaRegistry

Registry.instance = FiboaRegistry()
