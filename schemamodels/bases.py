# SPDX-FileCopyrightText: 2023-2026 Civic Hacker LLC
# SPDX-License-Identifier: GPL-3.0-or-later

from abc import ABC, abstractmethod
from collections.abc import Callable
from contextlib import contextmanager
from functools import partial
from operator import contains, ge, gt, le, lt, mod, not_
from typing import Any, AnyStr, ClassVar, Protocol, TypeVar, get_args

from schemamodels import exceptions as e
from schemamodels.constants import JSON_TYPE_MAP


class BaseErrorHandler(ABC):
    @classmethod
    @abstractmethod
    def apply(cls, f: Callable) -> Callable:
        raise NotImplementedError()

    @classmethod
    def __subclasshook__(cls, klass):
        if cls is BaseErrorHandler and "apply" in klass.__dict__:
            return True
        return NotImplementedError()


class BaseRenderer(ABC):
    @classmethod
    @abstractmethod
    def apply(cls, f: Callable) -> Callable:
        raise NotImplementedError()

    @classmethod
    def __subclasshook__(cls, klass):
        if cls is BaseRenderer and "apply" in klass.__dict__:
            return True
        return NotImplementedError()


A = TypeVar("A")
T = TypeVar("T", bound=str)
N = TypeVar("N", int, float)
S = TypeVar("S", bound=None)
C = TypeVar("C", list, tuple)
O = TypeVar("O", bound=dict)
B = TypeVar("B", bound=bool)


def validate_subschema(subschema: dict, value: Any) -> bool:
    if not isinstance(subschema, dict):
        return True
    if "type" in subschema:
        t = subschema["type"]
        if t == "string" and not isinstance(value, str):
            return False
        if t == "integer" and (not isinstance(value, int) or type(value) is bool):
            return False
        if t == "number" and (
            not isinstance(value, (int, float)) or type(value) is bool
        ):
            return False
        if t == "boolean" and type(value) is not bool:
            return False
        if t == "array" and not isinstance(value, (list, tuple)):
            return False
        if t == "object" and not isinstance(value, dict):
            return False
        if t == "null" and value is not None:
            return False
    if "minimum" in subschema and not (value >= subschema["minimum"]):
        return False
    if "maximum" in subschema and not (value <= subschema["maximum"]):
        return False
    if "exclusiveMinimum" in subschema and not (value > subschema["exclusiveMinimum"]):
        return False
    if "exclusiveMaximum" in subschema and not (value < subschema["exclusiveMaximum"]):
        return False
    if "multipleOf" in subschema and value % subschema["multipleOf"] != 0:
        return False
    if "maxLength" in subschema and not (len(value) <= subschema["maxLength"]):
        return False
    if "minLength" in subschema and not (len(value) >= subschema["minLength"]):
        return False
    if "enum" in subschema and not (value in subschema["enum"]):
        return False
    if "not" in subschema and validate_subschema(subschema["not"], value):
        return False
    if "anyOf" in subschema and not any(
        validate_subschema(s, value) for s in subschema["anyOf"]
    ):
        return False
    if "allOf" in subschema and not all(
        validate_subschema(s, value) for s in subschema["allOf"]
    ):
        return False
    return not (
        "oneOf" in subschema
        and sum(1 for s in subschema["oneOf"] if validate_subschema(s, value)) != 1
    )


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

        if hasattr(obj, "__dict__") and self._name in obj.__dict__:
            return obj.__dict__[self._name]

        return self.__dict__.get(self._name, self._default)

    def __set__(self, obj, value):
        if hasattr(self, "__orig_bases__") and self.__orig_bases__:
            args = get_args(self.__orig_bases__[0])
            if args:
                ttype = args[0]
                constraints = getattr(ttype, "__constraints__", None)
                if constraints:
                    if not isinstance(value, constraints):
                        raise e.ValueTypeViolation(
                            f"failed field constraints: {constraints}"
                        )
                else:
                    bound = getattr(ttype, "__bound__", None)
                    if bound and not isinstance(value, bound):
                        raise e.ValueTypeViolation(f"failed field constraints: {bound}")

        if isinstance(self._metadata, dict):
            if "anyOf" in self._metadata and not any(
                validate_subschema(s, value) for s in self._metadata["anyOf"]
            ):
                raise e.SubSchemaFailureViolation("all of the subschemas failed")
            if "allOf" in self._metadata and not all(
                validate_subschema(s, value) for s in self._metadata["allOf"]
            ):
                raise e.SubSchemaFailureViolation("at least one subschema failed")
            if "oneOf" in self._metadata and (
                sum(1 for s in self._metadata["oneOf"] if validate_subschema(s, value))
                != 1
            ):
                raise e.SubSchemaFailureViolation(
                    "none or multiple of the subschemas failed"
                )
            if "not" in self._metadata and validate_subschema(
                self._metadata["not"], value
            ):
                raise e.SubSchemaFailureViolation("subschema failed")
            if "enum" in self._metadata and value not in self._metadata["enum"]:
                raise e.ValueTypeViolation(
                    f"{self._name}={value} =/= enum={self._metadata['enum']} constraint fails"
                )


class ArrayDescriptor(JSONSchemaFieldDescriptor[C]):
    def __init__(self, *, default=None, metadata=None) -> None:
        super().__init__(default=default, metadata=metadata or {})

    def __set__(self, obj, value):
        if not isinstance(value, (list, tuple)):
            raise e.ValueTypeViolation("expected array")
        super().__set__(obj, value)
        if hasattr(obj, "__dict__"):
            obj.__dict__[self._name] = value
        self.__dict__[self._name] = value


class BooleanDescriptor(JSONSchemaFieldDescriptor[B]):
    def __init__(self, *, default=None, metadata=None) -> None:
        super().__init__(default=default, metadata=metadata or {})

    def __set__(self, obj, value):
        if not isinstance(value, bool):
            raise e.ValueTypeViolation("expected boolean")
        super().__set__(obj, value)
        if hasattr(obj, "__dict__"):
            obj.__dict__[self._name] = value
        self.__dict__[self._name] = value


class ObjectDescriptor(JSONSchemaFieldDescriptor[O]):
    def __init__(self, *, default=None, metadata=None) -> None:
        super().__init__(default=default, metadata=metadata or {})

    def __set__(self, obj, value):
        if not isinstance(value, dict):
            raise e.ValueTypeViolation("expected object")
        super().__set__(obj, value)
        if hasattr(obj, "__dict__"):
            obj.__dict__[self._name] = value
        self.__dict__[self._name] = value


class NullDescriptor(JSONSchemaFieldDescriptor[S]):
    def __init__(self, *, default=None, metadata=None) -> None:
        super().__init__(default=default, metadata=metadata or {})

    def __set__(self, obj, value):
        if value is not None:
            raise e.ValueTypeViolation("expected null")
        super().__set__(obj, value)
        if hasattr(obj, "__dict__"):
            obj.__dict__[self._name] = value
        self.__dict__[self._name] = value


class CollectionDescriptor(JSONSchemaFieldDescriptor[C]):
    COMPARISONS: ClassVar[dict] = {
        "maxLength": {
            "comparator": lambda d: partial(lambda bound, v: len(v) <= bound, d),
            "errorClass": e.LengthConstraintViolation,
        },
        "minLength": {
            "comparator": lambda d: partial(lambda bound, v: len(v) >= bound, d),
            "errorClass": e.LengthConstraintViolation,
        },
    }

    def __init__(self, *, default: Any = None, metadata: Any = None) -> None:
        super().__init__(default=default, metadata=metadata or {})

    def __set__(self, obj, value):
        if not isinstance(value, (list, tuple, set)):
            raise e.ValueTypeViolation("expected collection")
        super().__set__(obj, value)

        for metakey, metaval in self._metadata.items():
            key = self.COMPARISONS.get(metakey, None)
            if not key:
                continue
            if not key.get("comparator")(metaval)(value):
                raise key.get("errorClass")(
                    f"{self._name}={value} =/= {metakey}={metaval} constraint fails"
                )

        if hasattr(obj, "__dict__"):
            obj.__dict__[self._name] = value
        self.__dict__[self._name] = value


class StringDescriptor(JSONSchemaFieldDescriptor[AnyStr]):
    COMPARISONS: ClassVar[dict] = {
        "maxLength": {
            "comparator": lambda d: partial(lambda bound, v: len(v) <= bound, d),
            "errorClass": e.LengthConstraintViolation,
        },
        "minLength": {
            "comparator": lambda d: partial(lambda bound, v: len(v) >= bound, d),
            "errorClass": e.LengthConstraintViolation,
        },
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
            if not key.get("comparator")(metaval)(value):
                raise key.get("errorClass")(
                    f"{self._name}={value} =/= {metakey}={metaval} constraint fails"
                )

        if hasattr(obj, "__dict__"):
            obj.__dict__[self._name] = value
        self.__dict__[self._name] = value


class IntegerDescriptor(JSONSchemaFieldDescriptor[int]):
    COMPARISONS: ClassVar[dict] = {
        "minimum": {
            "comparator": lambda d: partial(le, d),
            "errorClass": e.RangeConstraintViolation,
        },
        "maximum": {
            "comparator": lambda d: partial(ge, d),
            "errorClass": e.RangeConstraintViolation,
        },
        "exclusiveMinimum": {
            "comparator": lambda d: partial(lt, d),
            "errorClass": e.RangeConstraintViolation,
        },
        "exclusiveMaximum": {
            "comparator": lambda d: partial(gt, d),
            "errorClass": e.RangeConstraintViolation,
        },
        "multipleOf": {
            "comparator": lambda d: partial(lambda d, n: mod(n, d) == 0, d),
            "errorClass": e.RangeConstraintViolation,
        },
    }

    def __init__(self, *, default=None, metadata=None):
        super().__init__(default=default, metadata=metadata or {})

    def __set__(self, obj, value):
        if isinstance(value, bool) or not isinstance(value, int):
            raise e.ValueTypeViolation("expected integer")
        super().__set__(obj, value)

        for metakey, metaval in self._metadata.items():
            key = self.COMPARISONS.get(metakey, None)
            if not key:
                continue
            if not key.get("comparator")(metaval)(value):
                raise key.get("errorClass")(
                    f"{self._name}={value} =/= {metakey}={metaval} constraint fails"
                )

        if hasattr(obj, "__dict__"):
            obj.__dict__[self._name] = value
        self.__dict__[self._name] = value


class NumberDescriptor(JSONSchemaFieldDescriptor[N]):
    COMPARISONS: ClassVar[dict] = {
        "minimum": {
            "comparator": lambda d: partial(le, d),
            "errorClass": e.RangeConstraintViolation,
        },
        "maximum": {
            "comparator": lambda d: partial(ge, d),
            "errorClass": e.RangeConstraintViolation,
        },
        "exclusiveMinimum": {
            "comparator": lambda d: partial(lt, d),
            "errorClass": e.RangeConstraintViolation,
        },
        "exclusiveMaximum": {
            "comparator": lambda d: partial(gt, d),
            "errorClass": e.RangeConstraintViolation,
        },
        "multipleOf": {
            "comparator": lambda d: partial(lambda d, n: mod(n, d) == 0, d),
            "errorClass": e.RangeConstraintViolation,
        },
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
            if not key.get("comparator")(metaval)(value):
                raise key.get("errorClass")(
                    f"{self._name}={value} =/= {metakey}={metaval} constraint fails"
                )

        if hasattr(obj, "__dict__"):
            obj.__dict__[self._name] = value
        self.__dict__[self._name] = value


class SpecialKeywordDescriptor(JSONSchemaFieldDescriptor[A]):
    MAP_TTYPE: ClassVar[dict] = {
        str: StringDescriptor,
        float: NumberDescriptor,
        int: IntegerDescriptor,
        bool: BooleanDescriptor,
        list: ArrayDescriptor,
        tuple: ArrayDescriptor,
        dict: ObjectDescriptor,
        type(None): NullDescriptor,
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
        except e.ValueTypeViolation:
            return False
        return True

    @contextmanager
    def dynamic_child_descriptors(self, obj, value):
        """

        Raises:
            ValueTypeViolation
        """
        yield
        if hasattr(obj, "__dict__"):
            obj.__dict__[self._name] = value
        self.__dict__[self._name] = value


class CoreModel(dict):
    COMPARISONS: ClassVar[dict] = {
        "type": lambda d: JSON_TYPE_MAP[d],
        "anyOf": lambda d: partial(
            lambda struct: __import__("schemamodels").generate_functors(struct), d
        ),
        "allOf": lambda d: partial(
            lambda struct: __import__("schemamodels").generate_functors(struct), d
        ),
        "oneOf": lambda d: partial(
            lambda struct: __import__("schemamodels").generate_functors(struct), d
        ),
        "not": lambda d: not_(d),
        "string": lambda d: isinstance(d, str),
        "integer": lambda d: isinstance(d, int),
        "number": lambda d: isinstance(d, (float, int)),
        "null": lambda d: d is None,
        "boolean": lambda d: isinstance(d, bool),
        "array": lambda d: isinstance(d, (list, tuple)),
        "minimum": lambda d: partial(le, d),
        "maximum": lambda d: partial(ge, d),
        "exclusiveMinimum": lambda d: partial(lt, d),
        "exclusiveMaximum": lambda d: partial(gt, d),
        "enum": lambda d: partial(contains, d),
        "maxLength": lambda d: partial(lambda bound, v: len(v) <= bound, d),
        "minLength": lambda d: partial(lambda bound, v: len(v) >= bound, d),
        "multipleOf": lambda d: partial(lambda d, n: mod(n, d) == 0, d),
    }

    def __call__(self, operand):
        return all(operation(operand) for operation in self.values())

    @property
    def type(self):
        return next(iter(self.values())).get("type", None)

    @property
    def name(self):
        return next(iter(self.keys()))