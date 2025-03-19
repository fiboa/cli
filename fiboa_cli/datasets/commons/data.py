from csv import DictReader
from os.path import dirname, join


def read_data_csv(name, **kwargs):
    path = join(dirname(dirname(__file__)), "data-files", name)
    with open(path, "r") as f:
        return list(DictReader(f, **kwargs))
