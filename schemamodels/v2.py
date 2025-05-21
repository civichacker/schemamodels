from typing import TypeVar, Generic


from schemamodels import exceptions as e


def process_keys(structure: dict):
    for k in set(structure.get('properties', {}).keys()) - {'$id', '$schema'}:
        yield k
T = TypeVar('T', bound=str)


class ScalarDescriptor(Generic[T]):

    JSON_TYPE_MAP = {
        'string': lambda d: isinstance(d, str),
        'integer': lambda d: isinstance(d, int),
        'number': lambda d: isinstance(d, (float, int)),
        'null': lambda d: d is None,
        'boolean': lambda d: isinstance(d, bool),
    }

    def __set_name__(self, o, name):
        self._name = "_" + name

    def __set__(self, obj, value: T):
        ttype = self.__orig_class__.__args__[0]
        if not isinstance(value, ttype):
            raise e.ValueTypeViolation()
        setattr(obj, self._name, value)


class CollectionDescriptor(Generic[T]):

    def __init__(self, *, default=None, metadata={}):
        self._metadata = metadata
        self._default = default

    def __set_name__(self, o, name):
        self._name = "_" + name

    def __set__(self, obj, value: T):
        if not isinstance(value, list):
            raise e.ValueTypeViolation()
        setattr(obj, self._name, value)

