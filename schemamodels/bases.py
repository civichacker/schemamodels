# SPDX-FileCopyrightText: 2023 Civic Hacker, LLC
# SPDX-License-Identifier: GPL-3.0-or-later

from abc import ABC, abstractmethod
from collections import deque, UserList
from functools import partial, reduce
from typing import Callable, Protocol, TypeVar, Generic, AnyStr, get_args
from schemamodels import exceptions as e
from operator import contains, le, ge, gt, lt, mod, not_


class BaseErrorHandler(ABC):

    @classmethod
    @abstractmethod
    def apply(cls, f: Callable) -> Callable:
        raise NotImplementedError()

    @classmethod
    def __subclasshook__(cls, klass):
        if cls is BaseErrorHandler:
            if "apply" in klass.__dict__:
                return True
        return NotImplementedError()


class BaseRenderer(ABC):

    @classmethod
    @abstractmethod
    def apply(cls, f: Callable) -> Callable:
        raise NotImplementedError()

    @classmethod
    def __subclasshook__(cls, klass):
        if cls is BaseRenderer:
            if "apply" in klass.__dict__:
                return True
        return NotImplementedError()


A = TypeVar('A')
T = TypeVar('T', bound=str)
N = TypeVar('N', int, float)
S = TypeVar('S', bound=None)
C = TypeVar('C', list, tuple)
O = TypeVar('O', bound=dict)
B = TypeVar('B', bound=bool)


class JSONSchemaFieldDescriptor(Protocol[A]):

    def __init__(self, *, default):
        self._default = default


    def __get__(self, obj, type):
        if obj is None:
            return self._default

        return self.__dict__.get(self._name, self._default)


    def __set__(self, obj, value):
        ttype = get_args(self.__orig_bases__[0])[0]

        if not isinstance(value, ttype.__constraints__):
            raise e.ValueTypeViolation()


class ArrayDescriptor(Generic[C]): pass
class BooleanDescriptor(JSONSchemaFieldDescriptor[S]): pass
class ObjectDescriptor(Generic[O]): pass

class StringDescriptor(JSONSchemaFieldDescriptor[AnyStr]):
    COMPARISONS = {
        'enum': {'comparator': lambda d: partial(contains, d), 'errorClass': e.ValueTypeViolation},
        'maxLength': {'comparator': lambda d: partial(lambda bound, v: len(v) <= bound, d), 'errorClass': e.LengthConstraintViolation},
        'not': {'comparator': lambda d: not isinstance(d, str), 'errorClass': e.ValueTypeViolation },
        'minLength': {'comparator': lambda d: partial(lambda bound, v: len(v) >= bound, d), 'errorClass': e.LengthConstraintViolation}
    }

    def __init__(self, *, default=None, metadata={}):
        self._metadata = metadata
        self._default = default

    def __set_name__(self, o, name):
        self._name = name

    def __set__(self, obj, value):
        super().__set__(obj, value)

        for metakey, metaval in self._metadata.items():
            key = self.COMPARISONS.get(metakey, None)
            if not key:
                raise Exception(f"Comparison keyword {metakey}:{key} is not supported")
            if not key.get('comparator')(metaval)(value):
                raise key.get('errorClass')(f'{self._name}={value} =/= {metakey}={metaval} constraint fails')

        self.__dict__[self._name] = value


class NumberDescriptor(JSONSchemaFieldDescriptor[N]):

    COMPARISONS = {
        'minimum': {'comparator': lambda d: partial(le, d), 'errorClass': e.ValueTypeViolation},
        'maximum': {'comparator': lambda d: partial(ge, d), 'errorClass': e.RangeConstraintViolation},
        'exclusiveMinimum': {'comparator': lambda d: partial(lt, d), 'errorClass': e.RangeConstraintViolation},
        'exclusiveMaximum': {'comparator': lambda d: partial(gt, d), 'errorClass': e.RangeConstraintViolation},
        'multipleOf': {'comparator': lambda d: partial(lambda d, n: mod(n, d) == 0, d), 'errorClass': e.RangeConstraintViolation},
        'not': {'comparator': lambda d: not_(d), 'errorClass': e.ValueTypeViolation },
    }

    # All fields support default arg
    def __init__(self, *, default=None, metadata={}):
        self._metadata = metadata
        self._default = default

    def __set_name__(self, o, name):
        self._name = name

    def __set__(self, obj, value):
        super().__set__(obj, value)

        for metakey, metaval in self._metadata.items():
            key = self.COMPARISONS.get(metakey, None)
            if not key:
                raise Exception(f"Comparison keyword {metakey}:{key} is not supported")
            if not key.get('comparator')(metaval)(value):
                raise key.get('errorClass')(f'{self._name}={value} =/= {metakey}={metaval} constraint fails')

        self.__dict__[self._name] = value


class CoreModel(dict):
    JSON_TYPE_MAP = {
        'string': lambda d: isinstance(d, str),
        'object': lambda d: isinstance(d, dict),
        'integer': lambda d: isinstance(d, int),
        'number': lambda d: isinstance(d, (float, int)),
        'null': lambda d: d is None,
        'boolean': lambda d: isinstance(d, bool),
        'array': lambda d: isinstance(d, (list, tuple)),
    }

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

    def __call__(self, operand):
        return all(operation(operand) for operation in self.values())

    @property
    def type(self):
        print(self.values())
        return list(self.values())[0].get('type', None)

    @property
    def name(self):
        return list(self.keys())[0]

    def map(self, operand):
        return TypeNode()

    def check(self, operand: dict):
        if self.name in self.keys() and self.JSON_TYPE_MAP.get(self.type)(operand.get(self.name)):
            return CoreModel(self)
        else:
            raise Exception()


class TypeNode(CoreModel):

    JSON_TYPE_MAP = {
        'string': lambda d: isinstance(d, str),
        'object': lambda d: isinstance(d, dict),
        'integer': lambda d: isinstance(d, int),
        'number': lambda d: isinstance(d, (float, int)),
        'null': lambda d: d is None,
        'boolean': lambda d: isinstance(d, bool),
        'array': lambda d: isinstance(d, (list, tuple)),
    }

    @property
    def type(self):
        return self.get('type', None)

    def check(self, value):
        return self.JSON_TYPE_MAP.get(self.type)(value)

    def map(self, value):
        return TypeNode()


class Tree(UserList):

    def __init__(self, bag={}):
        self.stack = deque()
        super().__init__(bag)

    def check(self, value):
        return all(d.check(value) for d in self.stack)

    def push(self, node):
        self.stack.append(node)

    def pop(self, node):
        return self.stack.pop()


class Node(CoreModel):

    JSON_TYPE_MAP = {
        'string': lambda d: isinstance(d, str),
        'object': lambda d: isinstance(d, dict),
        'integer': lambda d: isinstance(d, int),
        'number': lambda d: isinstance(d, (float, int)),
        'null': lambda d: d is None,
        'boolean': lambda d: isinstance(d, bool),
        'array': lambda d: isinstance(d, (list, tuple)),
    }

    @property
    def type(self):
        return self.data.get('type', None)

    def check(self, value):
        return self.JSON_TYPE_MAP.get(self.type)(value)
