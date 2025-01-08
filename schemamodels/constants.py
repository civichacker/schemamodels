from functools import partial
from operator import gt, ge, lt, le, mod, contains
from collections import ChainMap


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

PORCELINE_KEYWORDS = [
    'value',
    'default',
    'anyOf',
    'allOf',
    'oneOf',
    'not',
    'description'
]


COLLECTIONS = {
    'anyOf': lambda d: partial(lambda struct: generate_functors(struct), d),
    'allOf': lambda d: partial(lambda struct: generate_functors(struct), d),
    'oneOf': lambda d: partial(lambda struct: generate_functors(struct), d),
}

COMPARISONS = {
    'type': lambda d: JSON_TYPE_MAP[d],
    'not': lambda d: not_(d),
    'minimum': lambda d: partial(le, d),
    'maximum': lambda d: partial(ge, d),
    'exclusiveMinimum': lambda d: partial(lt, d),
    'exclusiveMaximum': lambda d: partial(gt, d),
    'enum': lambda d: partial(contains, d),
    'maxLength': lambda d: partial(lambda bound, v: len(v) <= bound, d),
    'minLength': lambda d: partial(lambda bound, v: len(v) >= bound, d),
    'multipleOf': lambda d: partial(lambda d, n: mod(n, d) == 0, d)
}

ALL_KEYWORDS = ChainMap(COLLECTIONS, COMPARISONS)
