from abc import ABC, abstractmethod
from dataclasses import make_dataclass, field
from re import sub
import importlib

from schemamodels import dynamic


JSON_TYPE_MAP = {
    'string': str,
    'integer': int,
    'number': float,
    'null': None
}

class Exporter(ABC):
    @abstractmethod
    def export(self): pass

    @classmethod
    def __subclasshook__(cls, C):
        if cls is MyIterable:
            if any("__iter__" in B.__dict__ for B in C.__mro__):
                return True
        return NotImplemented


def generate_classname(title: str) -> str:
    return sub(r'(-|_)+', '', title.title())


class SchemaModelFactory:
    def __init__(self, schemas=[], allow_remote=False):
        self.dmod = importlib.import_module('schemamodels.dynamic')

    def register(self, schema: dict) -> bool:
        if schema.get('type', None) != 'object':
            return False
        fields = list()
        fields_with_defaults = list()
        required_fields = schema.get('required', [])
        for k,v in schema['properties'].items():
            entry = (k, JSON_TYPE_MAP.get(v.get('type')))
            if len(required_fields) > 0 and k not in required_fields:
                entry += (field(default=None), )
                fields_with_defaults.append(entry)
            elif'default' in v.keys():
                entry += (field(default=v.get('default')), )
                fields_with_defaults.append(entry)
            else:
                fields.append(entry)
        C = make_dataclass(
            generate_classname(schema.get('title')),
            fields + fields_with_defaults,
            frozen=True
        )
        setattr(self.dmod, generate_classname(schema.get('title')), C)
        return True
