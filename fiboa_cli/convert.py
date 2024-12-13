import importlib
import os

from .convert_utils import BaseConverter
from .util import log

IGNORED_DATASET_FILES = ["__init__.py", "template.py"]

def convert(
        dataset,
        output_file,
        variant = None,
        input_files = None,
        cache = None,
        source_coop_url = None,
        collection = False,
        compression = None,
        geoparquet1 = False,
        mapping_file = None,
        original_geometries = False,
    ):
    if dataset in IGNORED_DATASET_FILES:
        raise Exception(f"'{dataset}' is not a converter")
    try:
        converter = read_converter(dataset)
    except ImportError as e:
        raise Exception(f"Converter for '{dataset}' not available or faulty: {e}")

    if hasattr(converter, "DATA_ACCESS") and not cache and not input_files:
        log("Data access is restricted. You need to manually get the data from the source.", "warning")
        log("Instructions for data access:", "warning")
        log(converter.DATA_ACCESS.strip(), "info")
        raise Exception("Provide the file through the `-i` parameter.")

    converter.convert(
        output_file,
        variant = variant,
        input_files = input_files,
        cache = cache,
        source_coop_url = source_coop_url,
        store_collection = collection,
        compression = compression,
        geoparquet1 = geoparquet1,
        mapping_file = mapping_file,
        original_geometries = original_geometries,
    )

def list_all_converter_ids():
    datasets = importlib.import_module(".datasets", package="fiboa_cli")
    files = os.listdir(datasets.__path__[0])
    return [f[:-3] for f in files if f.endswith(".py") and f not in IGNORED_DATASET_FILES]

def list_all_converters(keys):
    converters = {}
    for id in list_all_converter_ids():
        obj = {}
        try:
            converter = read_converter(id)
            for key in keys:
                if isinstance(converter, BaseConverter):
                    value = getattr(converter, key.lower())
                else:
                    value = getattr(converter, key, None)

                if key == "SOURCES" and isinstance(value, dict):
                    value = ", ".join(list(value.keys()))
                elif key == "LICENSE" and isinstance(value, dict):
                    value = value["href"]
                elif key == "PROVIDERS" and isinstance(value, list):
                    value = ", ".join(list(map(lambda x: x["name"], value)))

                obj[key] = value

            converters[id] = obj
        except ImportError:
            pass
    return converters


def read_converter(_id):
    module_name = f".datasets.{_id}"
    module = importlib.import_module(module_name, package="fiboa_cli")
    if not hasattr(module, "convert"):
        try:
            clazz = next(v for v in module.__dict__.values()
                         if type(v) is type and issubclass(v, BaseConverter) and v != BaseConverter)
            return clazz()
        except StopIteration:
            log("Missing convert function or Converter class for module {_id}", "warning")
    return module
