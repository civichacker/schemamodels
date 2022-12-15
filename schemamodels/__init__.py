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

    nodes = process_functors(final_form)

    if len([n for n in nodes if not n.get('type', True)]) > 0:
        raise e.ValueTypeViolation("incorrect type assigned to JSON property")
    if len([n for n in nodes if not n.get('maximum', True)]) > 0:
        raise e.RangeConstraintViolation("violates range contraint")
    if len([n for n in nodes if not n.get('exclusiveMaximum', True)]) > 0:
        raise e.RangeConstraintViolation("violates range contraint")
    if len([n for n in nodes if not n.get('exclusiveMinimum', True)]) > 0:
        raise e.RangeConstraintViolation("violates range contraint")
    if len([n for n in nodes if not n.get('minimum', True)]) > 0:
        raise e.RangeConstraintViolation("violates range contraint")
    if len([n for n in nodes if not n.get('multiplesOf', True)]) > 0:
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
            field_meta = dict()
            entry = (k, )
            if v.get('type', None):
                entry += (JSON_TYPE_MAP.get(v.get('type')), )
            elif 'anyOf' in v.keys() and 'type' not in v.keys():
                entry += (None, )
                for inner in v.get('anyOf'):
                    print(inner)
                    print(list(map(COMPARISONS.get, inner.keys())))
            else:
                entry += (1, )
            if k in required_fields:
                field_spec.update(init=True)

            if 'default' in v.keys():
                field_spec.update(default=v.get('default'))
            else:
                field_spec.update(default=None)

            field_meta = generate_functors(v)
            field_spec.update(metadata=field_meta)

            entry += (field(**field_spec), )
            fields.append(entry)

        dklass = partial(
            make_dataclass,
            klassname,
            fields + fields_with_defaults,
            frozen=True,
            namespace={
                '_errorhandler': self.error_handler.apply,
                '_renderer': self.renderer.apply,
                '__post_init__': lambda instance: constraints(instance)._errorhandler(instance)._renderer(instance)
            })
        if sys.version_info.major == 3 and sys.version_info.minor >= 10:
            dataklass = dklass(slots=True)
        else:
            dataklass = dklass()
        setattr(self.dmod,
                klassname,
                dataklass)
        return True
