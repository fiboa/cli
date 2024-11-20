class DictObject(object):
    def __init__(self, dict_):
        self.__dict__.update(dict_)
