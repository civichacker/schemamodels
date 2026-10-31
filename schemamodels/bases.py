# SPDX-FileCopyrightText: 2023 Civic Hacker, LLC
# SPDX-License-Identifier: GPL-3.0-or-later

from abc import ABC, abstractmethod
from functools import partial
from typing import Callable, Protocol, TypeVar, Generic, AnyStr, get_args, Any
from schemamodels import exceptions as e
from operator import contains, le, ge, gt, lt, mod, not_
from contextlib import contextmanager

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
U = TypeVar('U', int, str)
T = TypeVar('T', bound=str)
N = TypeVar('N', int, float)
S = TypeVar('S', bound=None)
C = TypeVar('C', list, tuple)
O = TypeVar('O', bound=dict)
B = TypeVar('B', bound=bool)


def validate_subschema(subschema: dict, value: Any) -> bool:
    if not isinstance(subschema, dict):
        return True
    if 'type' in subschema:
        t = subschema['type']
        if t == 'string' and not isinstance(value, str):
            return False
        if t == 'integer' and (not isinstance(value, int) or type(value) is bool):
            return False
        if t == 'number' and (not isinstance(value, (int, float)) or type(value) is bool):
            return False
        if t == 'boolean' and type(value) is not bool:
            return False
        if t == 'array' and not isinstance(value, (list, tuple)):
            return False
        if t == 'null' and value is not None:
            return False
    if 'minimum' in subschema and not (value >= subschema['minimum']):
        return False
    if 'maximum' in subschema and not (value <= subschema['maximum']):
        return False
    if 'exclusiveMinimum' in subschema and not (value > subschema['exclusiveMinimum']):
        return False
    if 'exclusiveMaximum' in subschema and not (value < subschema['exclusiveMaximum']):
        return False
    if 'multipleOf' in subschema and not (value % subschema['multipleOf'] == 0):
        return False
    if 'maxLength' in subschema and not (len(value) <= subschema['maxLength']):
        return False
    if 'minLength' in subschema and not (len(value) >= subschema['minLength']):
        return False
    if 'enum' in subschema and not (value in subschema['enum']):
        return False
    if 'not' in subschema and validate_subschema(subschema['not'], value):
        return False
    if 'anyOf' in subschema and not any(validate_subschema(s, value) for s in subschema['anyOf']):
        return False
    if 'allOf' in subschema and not all(validate_subschema(s, value) for s in subschema['allOf']):
        return False
    if 'oneOf' in subschema and sum(1 for s in subschema['oneOf'] if validate_subschema(s, value)) != 1:
        return False
    return True


class JSONSchemaFieldDescriptor(Protocol[A]):

    def __init__(self, *, default: Any = None, metadata: Any = None) -> None:
        self.__orig_bases__ = None
        self._default = default
        self._metadata = metadata or {}

    def __set_name__(self, o, name):
        self._name = name

    def __get__(self, obj, type=None):
        if obj is None:
            return self._default

        if hasattr(obj, '__dict__') and self._name in obj.__dict__:
            return obj.__dict__[self._name]

        return self.__dict__.get(self._name, self._default)

    def __set__(self, obj, value):
        if hasattr(self, '__orig_bases__') and self.__orig_bases__:
            args = get_args(self.__orig_bases__[0])
            if args:
                ttype = args[0]
                constraints = getattr(ttype, '__constraints__', None)
                if constraints:
                    if not isinstance(value, constraints):
                        raise e.ValueTypeViolation(f'failed field constraints: {constraints}')
                else:
                    bound = getattr(ttype, '__bound__', None)
                    if bound and not isinstance(value, bound):
                        raise e.ValueTypeViolation(f'failed field constraints: {bound}')

        if isinstance(self._metadata, dict):
            if 'allOf' in self._metadata:
                if not all(validate_subschema(s, value) for s in self._metadata['allOf']):
                    raise e.SubSchemaFailureViolation("at least one subschema failed")
            if 'oneOf' in self._metadata:
                if sum(1 for s in self._metadata['oneOf'] if validate_subschema(s, value)) != 1:
                    raise e.SubSchemaFailureViolation("none or multiple of the subschemas failed")
            if 'not' in self._metadata:
                if validate_subschema(self._metadata['not'], value):
                    raise e.SubSchemaFailureViolation("subschema failed")


class ArrayDescriptor(JSONSchemaFieldDescriptor[C]):
    def __init__(self, *, default=None, metadata=None) -> None:
        super().__init__(default=default, metadata=metadata or {})

    def __set__(self, obj, value):
        if not isinstance(value, (list, tuple)):
            raise e.ValueTypeViolation("expected array")
        super().__set__(obj, value)
        if hasattr(obj, '__dict__'):
            obj.__dict__[self._name] = value
        self.__dict__[self._name] = value


class BooleanDescriptor(JSONSchemaFieldDescriptor[B]):
    def __init__(self, *, default=None, metadata=None) -> None:
        super().__init__(default=default, metadata=metadata or {})

    def __set__(self, obj, value):
        if not isinstance(value, bool):
            raise e.ValueTypeViolation("expected boolean")
        super().__set__(obj, value)
        if hasattr(obj, '__dict__'):
            obj.__dict__[self._name] = value
        self.__dict__[self._name] = value


class ObjectDescriptor(JSONSchemaFieldDescriptor[O]):
    def __init__(self, *, default=None, metadata=None) -> None:
        super().__init__(default=default, metadata=metadata or {})

    def __set__(self, obj, value):
        if not isinstance(value, dict):
            raise e.ValueTypeViolation("expected object")
        super().__set__(obj, value)
        if hasattr(obj, '__dict__'):
            obj.__dict__[self._name] = value
        self.__dict__[self._name] = value


class CollectionDescriptor(JSONSchemaFieldDescriptor[C]):
    COMPARISONS = {
        'enum': {'comparator': lambda d: partial(contains, d), 'errorClass': e.ValueTypeViolation},
        'maxLength': {'comparator': lambda d: partial(lambda bound, v: len(v) <= bound, d), 'errorClass': e.LengthConstraintViolation},
        'not': {'comparator': lambda d: not isinstance(d, str), 'errorClass': e.ValueTypeViolation },
        'minLength': {'comparator': lambda d: partial(lambda bound, v: len(v) >= bound, d), 'errorClass': e.LengthConstraintViolation}
    }

    def __init__(self, *, default: Any = None, metadata: Any = None) -> None:
        super().__init__(default=default, metadata=metadata or {})

    def __set__(self, obj, value):
        super().__set__(obj, value)

        for metakey, metaval in self._metadata.items():
            key = self.COMPARISONS.get(metakey, None)
            if not key:
                continue
            if not key.get('comparator')(metaval)(value):
                raise key.get('errorClass')(f'{self._name}={value} =/= {metakey}={metaval} constraint fails')

        if hasattr(obj, '__dict__'):
            obj.__dict__[self._name] = value
        self.__dict__[self._name] = value



class StringDescriptor(JSONSchemaFieldDescriptor[AnyStr]):
    COMPARISONS = {
        'enum': {'comparator': lambda d: partial(contains, d), 'errorClass': e.ValueTypeViolation},
        'maxLength': {'comparator': lambda d: partial(lambda bound, v: len(v) <= bound, d), 'errorClass': e.LengthConstraintViolation},
        'not': {'comparator': lambda d: not isinstance(d, str), 'errorClass': e.ValueTypeViolation },
        'minLength': {'comparator': lambda d: partial(lambda bound, v: len(v) >= bound, d), 'errorClass': e.LengthConstraintViolation}
    }

    def __init__(self, *, default=None, metadata=None):
        super().__init__(default=default, metadata=metadata or {})

    def __set__(self, obj, value):
        if not isinstance(value, (str, bytes)):
            raise e.ValueTypeViolation("expected string")
        super().__set__(obj, value)

        for metakey, metaval in self._metadata.items():
            key = self.COMPARISONS.get(metakey, None)
            if not key:
                continue
            if not key.get('comparator')(metaval)(value):
                raise key.get('errorClass')(f'{self._name}={value} =/= {metakey}={metaval} constraint fails')

        if hasattr(obj, '__dict__'):
            obj.__dict__[self._name] = value
        self.__dict__[self._name] = value


# noinspection PyProtocol
class NumberDescriptor(JSONSchemaFieldDescriptor[N]):

    COMPARISONS = {
        'minimum': {'comparator': lambda d: partial(le, d), 'errorClass': e.RangeConstraintViolation},
        'maximum': {'comparator': lambda d: partial(ge, d), 'errorClass': e.RangeConstraintViolation},
        'exclusiveMinimum': {'comparator': lambda d: partial(lt, d), 'errorClass': e.RangeConstraintViolation},
        'exclusiveMaximum': {'comparator': lambda d: partial(gt, d), 'errorClass': e.RangeConstraintViolation},
        'multipleOf': {'comparator': lambda d: partial(lambda d, n: mod(n, d) == 0, d), 'errorClass': e.RangeConstraintViolation},
        'not': {'comparator': lambda d: not_(d), 'errorClass': e.ValueTypeViolation },
    }

    def __init__(self, *, default=None, metadata=None):
        super().__init__(default=default, metadata=metadata or {})

    def __set__(self, obj, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise e.ValueTypeViolation("expected number")
        super().__set__(obj, value)

        for metakey, metaval in self._metadata.items():
            key = self.COMPARISONS.get(metakey, None)
            if not key:
                continue
            if not key.get('comparator')(metaval)(value):
                raise key.get('errorClass')(f'{self._name}={value} =/= {metakey}={metaval} constraint fails')

        if hasattr(obj, '__dict__'):
            obj.__dict__[self._name] = value
        self.__dict__[self._name] = value

class SpecialKeywordDescriptor(JSONSchemaFieldDescriptor[A]):

    MAP_TTYPE = {
        str: StringDescriptor,
        float: NumberDescriptor,
        int: NumberDescriptor,
        bool: BooleanDescriptor,
        list: ArrayDescriptor,
        dict: ObjectDescriptor,
    }
    def __init__(self, *, default=None, metadata=None):
        super().__init__(default=default, metadata=metadata or {})

    @classmethod
    def process_child_descriptors(cls, _name: str, c: A, value) -> bool:
        descriptor_cls = cls.MAP_TTYPE.get(c)
        if descriptor_cls is None:
            return True
        des = descriptor_cls()
        des.__set_name__(None, _name)
        try:
            des.__set__(_name, value)
        except Exception:
            return False
        return True

    @contextmanager
    def dynamic_child_descriptors(self, obj, value):
        try:
            yield
            if hasattr(obj, '__dict__'):
                obj.__dict__[self._name] = value
            self.__dict__[self._name] = value
        except Exception:
            raise


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

