import sys
from dataclasses import make_dataclass, field, fields as fs
from re import sub
import importlib
from operator import gt, ge, lt, le, mod
from typing import Callable

from functools import partial

from schemamodels import exceptions as e, bases


JSON_TYPE_MAP = {
    'string': lambda d: isinstance(d, str),
    'integer': lambda d: isinstance(d, int),
    'number': lambda d: isinstance(d, (float, int)),
    'null': lambda d: d is None,
    'boolean': lambda d: isinstance(d, bool),
    'array': lambda d: isinstance(d, (list, tuple)),
}

RANGE_KEYWORDS = {
    'minimum': le,
    'maximum': ge,
    'exclusiveMinimum': lt,
    'exclusiveMaximum': gt,
    'multiplesOf': lambda d, n: mod(n, d) == 0
}

LOGICAL_KEYWORDS = {
    'anyOf': any
}


PORCELINE_KEYWORDS = ['value', 'default']

COMPARISONS = {
    'type': lambda d: JSON_TYPE_MAP[d],
    'anyOf': RANGE_KEYWORDS,
    'string': lambda d: isinstance(d, str),
    'integer': lambda d: isinstance(d, int),
    'number': lambda d: isinstance(d, (float, int)),
    'null': lambda d: d is None,
    'boolean': lambda d: isinstance(d, bool),
    'array': lambda d: isinstance(d, (list, tuple)),
    'minimum': lambda d: partial(le, d),
    'maximum': lambda d: partial(ge, d),
    'exclusiveMinimum': lambda d: partial(lt, d),
    'exclusiveMaximum': lambda d: partial(gt, d),
    'multiplesOf': lambda d: partial(lambda d, n: mod(n, d) == 0, d)
}


class DefaultErrorHandler(bases.BaseErrorHandler):

    @classmethod
    def apply(cls, f: Callable) -> Callable:
        return f


class DefaultRenderer(bases.BaseRenderer):

    @classmethod
    def apply(cls, f: Callable) -> Callable:
        return f


def generate_classname(title: str) -> str:
    return sub(r'(-|_)+', '', title.title())


def generate_functors(struct):
    return {k: COMPARISONS[k](v) for k, v in struct.items() if k not in PORCELINE_KEYWORDS}


def process_functors(nodes):
    t = list()
    for node in nodes:
        t.append({k: v(node['value']) for k, v in node['metadata'].items()})
    return t


def constraints(dataclass_instance):
    fields_with_metadata = filter(lambda f: f.metadata != {}, fs(dataclass_instance))
    final_form = map(lambda f: {'value': getattr(dataclass_instance,  f.name), 'name': f.name, 'metadata': f.metadata}, fields_with_metadata)
    if not all(map(lambda i: all([pop(i['value']) for pop in i['metadata'].values()]), final_form)):
        raise e.RangeConstraintViolation("violates range contraint")
    return dataclass_instance


def value_checks(dataclass_instance):
    all_the_fields = fs(dataclass_instance)
    if not all(isinstance(getattr(dataclass_instance, f.name), f.type) for f in all_the_fields if f.type):
        raise e.ValueTypeViolation("incorrect type assigned to JSON property")
    return dataclass_instance


class SchemaModelFactory:
    def __init__(self, schemas=[], error_handler=DefaultErrorHandler, renderer=DefaultRenderer):
        self.error_handler = error_handler
        self.renderer = renderer
        self.___check_custom_hooks()
        self.dmod = importlib.import_module('schemamodels.dynamic')
        list(map(lambda s: self.register(s), schemas))  # FIXME: find another way to 'process' the map

    def ___check_custom_hooks(self):
        self.error_handler()
        self.renderer()

    def register(self, schema: dict) -> bool:
        reqkws = {'title', 'type', 'properties'}
        if not reqkws <= schema.keys() or schema.get('type', None) != 'object':
            return False
        else:
            klassname = generate_classname(schema.get('title'))
        fields = list()
        fields_with_defaults = list()
        required_fields = schema.get('required', [])
        for k, v in schema['properties'].items():
            field_spec = dict()
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
            elif {'anyOf'} < v.keys():
                fields.append(entry)
                return False
            else:
                fields.append(entry)
        dklass = partial(
            make_dataclass,
            klassname,
            fields + fields_with_defaults,
            frozen=True,
            namespace={
                '_errorhandler': self.error_handler.apply,
                '_renderer': self.renderer.apply,
                '__post_init__': lambda instance: constraints(value_checks(instance))._errorhandler(instance)._renderer(instance)
            })
        if sys.version_info.major == 3 and sys.version_info.minor >= 10:
            dataklass = dklass(slots=True)
        else:
            dataklass = dklass()
        setattr(self.dmod,
                klassname,
                dataklass)
        return True
