from abc import ABC, abstractmethod
from dataclasses import make_dataclass, field, fields as fs
from re import sub
import importlib
from operator import gt, ge, lt, le

from functools import partial

from schemamodels import dynamic


JSON_TYPE_MAP = {
    'string': str,
    'integer': int,
    'number': float,
    'null': None,
    'boolean': bool,
    'array': list
}

RANGE_KEYWORDS = {
        'minimum': le,
        'maximum': ge,
        'exclusiveMinimum': lt,
        'exclusiveMaximum': gt
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


def process_metadata_expression(dataclass_instance):
    fields_with_metadata = filter(lambda f: f.metadata != {}, fs(dataclass_instance))
    final_form = map(lambda f: {'value': getattr(dataclass_instance,  f.name), 'name': f.name, 'metadata': f.metadata}, fields_with_metadata)
    if not all(map(lambda i: all([pop(i['value']) for pop in i['metadata'].values()]) , final_form)):
        raise Exception
    return True


def process_value_checks(dataclass_instance):
    all_the_fields = fs(dataclass_instance)
    if not all(isinstance(getattr(dataclass_instance, f.name), f.type) for f in all_the_fields):
        raise Exception
    return True



class SchemaModelFactory:
    def __init__(self, schemas=[], allow_remote=False):
        self.dmod = importlib.import_module('schemamodels.dynamic')
        list(map(lambda s: self.register(s), schemas))  # FIXME: find another way to 'process' the map

    def register(self, schema: dict) -> bool:
        if not schema.get('title', None):
            return False
        else:
            klassname = generate_classname(schema.get('title'))
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
        setattr(self.dmod,
                klassname,
                make_dataclass(
                    klassname,
                    fields + fields_with_defaults,
                    frozen=True,
                    namespace={
                        '__post_init__': lambda self: process_value_checks(self) or process_metadata_expression(self)
                    })
        )
        return True
