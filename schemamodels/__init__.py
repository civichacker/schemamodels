# SPDX-FileCopyrightText: 2023 Civic Hacker, LLC
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
from dataclasses import make_dataclass, field, fields as fs, asdict, Field
from dataclasses import MISSING
from re import sub
import importlib
from operator import gt, ge, lt, le, mod, xor, not_, contains
from typing import Callable
from collections import deque

from functools import partial, reduce

from schemamodels import exceptions as e, bases


DEFAULT_FACTORIES = {
    'string': str,
    'integer': int,
    'number': float,
    'null': None,
    'boolean': bool,
    'not': callable,
    'anyof': callable,
    'allof': callable,
    'array': list,
}


JSON_TYPE_MAP = {
    'string': lambda d: isinstance(d, str),
    'integer': lambda d: isinstance(d, int),
    'number': lambda d: isinstance(d, (float, int)),
    'null': lambda d: d is None,
    'boolean': lambda d: isinstance(d, bool),
    'array': lambda d: isinstance(d, (list, tuple)),
}

PORCELINE_KEYWORDS = ['value', 'default', 'anyOf', 'allOf', 'oneOf', 'not', 'description']

COMPARISONS = {
    'type': lambda d: JSON_TYPE_MAP[d],
    'anyOf': lambda d: partial(lambda struct: generate_functors(struct), d),
    'allOf': lambda d: partial(lambda struct: generate_functors(struct), d),
    'oneOf': lambda d: partial(lambda struct: generate_functors(struct), d),
    'not': lambda d: not_(d),
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
    'enum': lambda d: partial(contains, d),
    'maxLength': lambda d: partial(lambda bound, v: len(v) <= bound, d),
    'minLength': lambda d: partial(lambda bound, v: len(v) >= bound, d),
    'multipleOf': lambda d: partial(lambda d, n: mod(n, d) == 0, d)
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
        for k, v in node['metadata'].items():
            if k == 'anyOf':
                ans_list = v(node["value"])
                t.append({k: any([all(m.values()) for m in ans_list])})
            elif k == 'allOf':
                ans_list = v(node["value"])
                t.append({k: all(all(m.values()) for m in ans_list)})
            elif k == 'oneOf':
                ans_list = v(node["value"])
                t.append({k: reduce(xor, [all(m.values()) for m in ans_list])})
            elif k == 'not':
                ans_list = [fun(node["value"]) for fun in v.values()]
                t.append({k: not_(all(ans_list))})
            else:
                ans_list = v(node["value"])
                t.append({k: ans_list})
    return t


def functor_eval(functors: Callable, value):
    return [{f: func[f](value) for f in func} for func in functors]


def constraints(dataclass_instance):
    fields_with_metadata = filter(lambda f: f.metadata != {}, fs(dataclass_instance))
    final_form = list(map(lambda f: {'value': getattr(dataclass_instance,  f.name), 'name': f.name, 'metadata': f.metadata}, fields_with_metadata))

    nodes = process_functors(final_form)

    if len([n for n in nodes if not n.get('not', True)]) > 0:
        raise e.SubSchemaFailureViolation("subschema failed")
    if len([n for n in nodes if not n.get('oneOf', True)]) > 0:
        raise e.SubSchemaFailureViolation("none or multiple of the subschemas failed")
    if len([n for n in nodes if not n.get('anyOf', True)]) > 0:
        raise e.SubSchemaFailureViolation("all of the subschemas failed")
    if len([n for n in nodes if not n.get('allOf', True)]) > 0:
        raise e.SubSchemaFailureViolation("at least one subschema failed")
    if len([n for n in nodes if not n.get('type', True)]) > 0:
        raise e.ValueTypeViolation("incorrect type assigned to JSON property")
    if len([n for n in nodes if not n.get('enum', True)]) > 0:
        raise e.ValueTypeViolation("string property much use declared enum values")
    if len([n for n in nodes if not n.get('maximum', True)]) > 0:
        raise e.RangeConstraintViolation("violates range contraint")
    if len([n for n in nodes if not n.get('exclusiveMaximum', True)]) > 0:
        raise e.RangeConstraintViolation("violates range contraint")
    if len([n for n in nodes if not n.get('exclusiveMinimum', True)]) > 0:
        raise e.RangeConstraintViolation("violates range contraint")
    if len([n for n in nodes if not n.get('minimum', True)]) > 0:
        raise e.RangeConstraintViolation("violates range contraint")
    if len([n for n in nodes if not n.get('multipleOf', True)]) > 0:
        raise e.RangeConstraintViolation("violates range contraint")
    if len([n for n in nodes if not n.get('maxLength', True)]) > 0:
        raise e.LengthConstraintViolation("violates length contraint")
    if len([n for n in nodes if not n.get('minLength', True)]) > 0:
        raise e.LengthConstraintViolation("violates length contraint")
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
        fields = deque()
        fields_with_defaults = deque()
        required_fields = schema.get('required', [])
        if schema.get('anyOf', None):  # Top-level anyOf
            funcs = [generate_functors(s) for s in schema['anyOf']]
            # Do something with this
        for k, v in schema['properties'].items():
            field_spec = dict()
            field_meta = dict()
            entry = (k, )
            if 'anyOf' in v:
                funcs = [generate_functors(s) for s in v['anyOf']]
                field_meta.update({'anyOf': partial(functor_eval, funcs)})
            if 'oneOf' in v:
                funcs = [generate_functors(s) for s in v['oneOf']]
                field_meta.update({'oneOf': partial(functor_eval, funcs)})
            if 'allOf' in v:
                funcs = [generate_functors(s) for s in v['allOf']]
                field_meta.update({'allOf': partial(functor_eval, funcs)})
            if 'not' in v:
                field_meta.update({'not': generate_functors(v.get('not'))})

            if v.get('type', None):
                entry += (JSON_TYPE_MAP.get(v.get('type')), )
                field_spec.update(default_factory=DEFAULT_FACTORIES[v.get('type')])
            else:
                print('not a built-in')
                entry += (1, )

            if 'default' in v.keys():
                field_spec.update(default=v.get('default', Field))
                field_spec.pop('default_factory', None)
            else:
                field_spec.update(default_factory=DEFAULT_FACTORIES.get(v.get('type'), str))

            field_meta.update(generate_functors(v))
            field_spec.update(metadata=field_meta)

            if k in required_fields:
                field_spec.update(default_factory=MISSING)
                field_spec.update(default=MISSING)

            entry += (field(**field_spec), )

            # print(entry)
            if not hasattr(entry, 'default'):
                fields.appendleft(entry)
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
                'tocsv': lambda self, header=False, fields=schema['properties'].keys(): f'{",".join(fields)}\n{",".join(map(lambda i: asdict(self)[i], fields))}' if header else ",".join(map(lambda i: asdict(self)[i], fields)),
                'tolist': lambda self: list(asdict(self).values()),
                'todict': lambda self: asdict(self),
                '__post_init__': lambda self: constraints(self)._errorhandler(self)._renderer(self)
            })
        if sys.version_info.major == 3 and sys.version_info.minor >= 10:
            dataklass = dklass(slots=True)
        else:
            dataklass = dklass()
        setattr(self.dmod,
                klassname,
                dataklass)
        return True
