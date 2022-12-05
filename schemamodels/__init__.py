import sys
from dataclasses import make_dataclass, field, fields as fs
from abc import ABC, abstractmethod
from re import sub
import importlib
from operator import gt, ge, lt, le
from typing import Callable

from functools import partial

from schemamodels import exceptions as e


JSON_TYPE_MAP = {
    'string': str,
    'integer': int,
    'number': (float, int),
    'null': None,
    'boolean': bool,
    'array': (list, tuple)
}

RANGE_KEYWORDS = {
        'minimum': le,
        'maximum': ge,
        'exclusiveMinimum': lt,
        'exclusiveMaximum': gt
}

class ErrorHandler(ABC):

    @classmethod
    @abstractmethod
    def apply(self, f: Callable):
        return f

    @classmethod
    def __subclasshook__(cls, C):
        if cls is ErrorHandler:
            if "apply" in C.__dict__:
                return True
        return NotImplemented


class Renderer(ABC):

    @classmethod
    @abstractmethod
    def apply(self, f: Callable) -> Callable:
        return f

    @classmethod
    def __subclasshook__(cls, C):
        if cls is Renderer:
            if "apply" in C.__dict__:
                return True
        return NotImplemented


def generate_classname(title: str) -> str:
    return sub(r'(-|_)+', '', title.title())


def constraints(dataclass_instance):
    fields_with_metadata = filter(lambda f: f.metadata != {}, fs(dataclass_instance))
    final_form = map(lambda f: {'value': getattr(dataclass_instance,  f.name), 'name': f.name, 'metadata': f.metadata}, fields_with_metadata)
    if not all(map(lambda i: all([pop(i['value']) for pop in i['metadata'].values()]), final_form)):
        raise e.RangeConstraintViolation("violates range contraint")
    return dataclass_instance


def value_checks(dataclass_instance):
    all_the_fields = fs(dataclass_instance)
    if not all(isinstance(getattr(dataclass_instance, f.name), f.type) for f in all_the_fields):
        raise e.ValueTypeViolation("incorrect type assigned to JSON property")
    return dataclass_instance


class SchemaModelFactory:
    def __init__(self, schemas=[]):
        self.dmod = importlib.import_module('schemamodels.dynamic')
        list(map(lambda s: self.register(s), schemas))  # FIXME: find another way to 'process' the map

    def register(self, schema: dict, error_handler = ErrorHandler, renderer = Renderer) -> bool:
        if not schema.get('title', None):
            return False
        else:
            klassname = generate_classname(schema.get('title'))
        if schema.get('type', None) != 'object':
            return False
        fields = list()
        fields_with_defaults = list()
        required_fields = schema.get('required', [])
        for k, v in schema['properties'].items():
            entry = (k, JSON_TYPE_MAP.get(v.get('type')))
            if len(required_fields) > 0 and k not in required_fields:
                entry += (field(default=None), )
                fields_with_defaults.append(entry)
            elif 'default' in v.keys():
                entry += (field(default=v.get('default')), )
                fields_with_defaults.append(entry)
            elif not set(RANGE_KEYWORDS.keys()).isdisjoint(set(v.keys())):
                # Detect range expression
                _range = list(set(RANGE_KEYWORDS.keys()).intersection(set(v)))
                metad = dict()
                if _range:
                    metad = {e: partial(RANGE_KEYWORDS.get(e), v.get(e)) for e in _range}
                entry += (field(metadata=metad), )
                fields.append(entry)

            else:
                fields.append(entry)
        dklass = partial(
            make_dataclass,
            klassname,
            fields + fields_with_defaults,
            frozen=True,
            namespace={
                '__post_init__': lambda self: process_value_checks(self) and process_metadata_expression(self)
            })
        if sys.version_info.major == 3 and sys.version_info.minor >= 10:
            dataklass = dklass(slots=True)
        else:
            dataklass = dklass()
        setattr(self.dmod,
                klassname,
                dataklass)
        return True
