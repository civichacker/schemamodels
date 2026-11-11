# SPDX-FileCopyrightText: 2023-2026 Civic Hacker LLC
# SPDX-License-Identifier: GPL-3.0-or-later

from abc import ABC, abstractmethod
from collections.abc import Callable
from contextlib import contextmanager
from contextvars import ContextVar
from functools import partial
from operator import contains, ge, gt, le, lt, mod, not_
from typing import Any, AnyStr, ClassVar, Protocol, Self, TypeVar, get_args

from schemamodels import exceptions as e, constants
from schemamodels.constants import JSON_TYPE_MAP, REQUIRED_MISSING


class ValidationCollector:
    def __init__(self) -> None:
        self.errors: list[e.SchemaViolation] = []
        self._token = None

    def __enter__(self) -> Self:
        self._token = _CURRENT_VALIDATION_COLLECTOR.set(self)
        return self

    def __exit__(self, *args) -> None:
        """

        :param args: This is really exc_type, exc_val, and exc_tb args
        :return:
        """
        if self._token is not None:
            _CURRENT_VALIDATION_COLLECTOR.reset(self._token)


_CURRENT_VALIDATION_COLLECTOR: ContextVar[ValidationCollector | None] = ContextVar(
    "_CURRENT_VALIDATION_COLLECTOR", default=None
)


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
O = TypeVar("O", bound=dict)  # noqa: E741
B = TypeVar("B", bound=bool)


def _json_equal(a: Any, b: Any) -> bool:
    if type(a) is not type(b):
        if (
            isinstance(a, (int, float))
            and isinstance(b, (int, float))
            and not isinstance(a, bool)
            and not isinstance(b, bool)
        ):
            return a == b
        return False
    if isinstance(a, (list, tuple)):
        return len(a) == len(b) and all(_json_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(_json_equal(a[k], b[k]) for k in a)
    return a == b


def _are_items_unique(v) -> bool:
    for i in range(len(v)):
        for j in range(i + 1, len(v)):
            if _json_equal(v[i], v[j]):
                return False
    return True


def validate_subschema(subschema: dict | bool, value: Any) -> bool:  # noqa: C901
    if isinstance(subschema, bool):
        return subschema
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
    if (
        "minimum" in subschema
        and isinstance(value, (int, float))
        and type(value) is not bool
        and not (value >= subschema["minimum"])
    ):
        return False
    if (
        "maximum" in subschema
        and isinstance(value, (int, float))
        and type(value) is not bool
        and not (value <= subschema["maximum"])
    ):
        return False
    if (
        "exclusiveMinimum" in subschema
        and isinstance(value, (int, float))
        and type(value) is not bool
        and not (value > subschema["exclusiveMinimum"])
    ):
        return False
    if (
        "exclusiveMaximum" in subschema
        and isinstance(value, (int, float))
        and type(value) is not bool
        and not (value < subschema["exclusiveMaximum"])
    ):
        return False
    if (
        "multipleOf" in subschema
        and isinstance(value, (int, float))
        and type(value) is not bool
        and value % subschema["multipleOf"] != 0
    ):
        return False
    if (
        "maxLength" in subschema
        and isinstance(value, str)
        and not (len(value) <= subschema["maxLength"])
    ):
        return False
    if (
        "minLength" in subschema
        and isinstance(value, str)
        and not (len(value) >= subschema["minLength"])
    ):
        return False
    if "enum" in subschema and not (value in subschema["enum"]):
        return False
    if "const" in subschema and not _json_equal(value, subschema["const"]):
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
    COMPARISONS: ClassVar[dict] = {}

    def __init__(self, *, default: Any = None, metadata: Any = None) -> None:
        self.__orig_bases__ = None
        self._default = default
        self._metadata = metadata or {}
        self._raw_enum = self._metadata.get("enum")
        self._enum = set(self._raw_enum) if self._raw_enum is not None else None
        self._any_of = self._metadata.get("anyOf")
        self._all_of = self._metadata.get("allOf")
        self._one_of = self._metadata.get("oneOf")
        self._not = self._metadata.get("not")
        self._has_subschemas = bool(
            self._any_of or self._all_of or self._one_of or (self._not is not None)
        )

    def __set_name__(self, o, name):
        self._name = name

    def __get__(self, obj, type=None):
        if obj is None:
            return self._default

        if hasattr(obj, "__dict__") and self._name in obj.__dict__:
            return obj.__dict__[self._name]

        return self.__dict__.get(self._name, self._default)

    def _validate_subschemas(self, value: Any) -> None:
        if self._any_of is not None and not any(
            validate_subschema(s, value) for s in self._any_of
        ):
            raise e.SubSchemaFailureViolation("all of the subschemas failed")
        if self._all_of is not None and not all(
            validate_subschema(s, value) for s in self._all_of
        ):
            raise e.SubSchemaFailureViolation("at least one subschema failed")
        if self._one_of is not None and (
            sum(1 for s in self._one_of if validate_subschema(s, value)) != 1
        ):
            raise e.SubSchemaFailureViolation(
                "none or multiple of the subschemas failed"
            )
        if self._not is not None and validate_subschema(self._not, value):
            raise e.SubSchemaFailureViolation("subschema failed")

    def __set__(self, obj, value):  # noqa: C901
        errors = (
            obj.__dict__.get("_validation_errors") if hasattr(obj, "__dict__") else None
        )
        try:
            if value is REQUIRED_MISSING:
                raise e.RequiredPropertyViolation(
                    f"{self._name} is a required property"
                )
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
                            raise e.ValueTypeViolation(
                                f"failed field constraints: {bound}"
                            )

            if self._enum is not None and value not in self._enum:
                raise e.ValueTypeViolation(
                    f"{self._name}={value} =/= enum={self._raw_enum} constraint fails"
                )
            if self._has_subschemas:
                self._validate_subschemas(value)
        except e.SchemaViolation as exc:
            if errors is not None:
                errors.append(exc)
                if hasattr(obj, "__dict__"):
                    obj.__dict__[self._name] = value
                else:
                    self.__dict__[self._name] = value
                return
            raise

        if hasattr(obj, "__dict__"):
            obj.__dict__[self._name] = value
        else:
            self.__dict__[self._name] = value


class ArrayDescriptor(JSONSchemaFieldDescriptor[C]):
    COMPARISONS: ClassVar[dict] = {
        "maxItems": {
            "comparator": lambda d: partial(lambda bound, v: 0 <= len(v) <= bound, d),
            "errorClass": e.ArrayLengthViolation,
        },
        "minItems": {
            "comparator": lambda d: partial(lambda bound, v: 0 <= bound <= len(v), d),
            "errorClass": e.ArrayLengthViolation,
        },
        "maxContains": {
            "comparator": lambda d: partial(
                lambda bound, v, contains=None: (
                    True
                    if contains is None
                    else (
                        sum(1 for item in v if validate_subschema(contains, item))
                        <= bound
                    )
                ),
                d,
            ),
            "errorClass": e.ArrayElementViolation,
        },
        "minContains": {
            "comparator": lambda d: partial(
                lambda bound, v, contains=None: (
                    True
                    if contains is None
                    else (
                        sum(1 for item in v if validate_subschema(contains, item))
                        >= bound
                    )
                ),
                d,
            ),
            "errorClass": e.ArrayElementViolation,
        },
        "uniqueItems": {
            "comparator": lambda d: partial(
                lambda unique, v: _are_items_unique(v) if unique else True, d
            ),
            "errorClass": e.ArrayUniqueElementViolation,
        },
    }

    def __init__(self, *, default=None, metadata=None) -> None:
        super().__init__(default=default, metadata=metadata or {})
        self._min_items = self._metadata.get("minItems")
        self._max_items = self._metadata.get("maxItems")
        self._unique_items = self._metadata.get("uniqueItems")
        self._contains = self._metadata.get("contains")
        self._min_contains = self._metadata.get("minContains")
        self._max_contains = self._metadata.get("maxContains")

    def __set__(self, obj, value):  # noqa: C901
        errors = (
            obj.__dict__.get("_validation_errors") if hasattr(obj, "__dict__") else None
        )
        try:
            if value is REQUIRED_MISSING:
                raise e.RequiredPropertyViolation(
                    f"{self._name} is a required property"
                )
            if not isinstance(value, (list, tuple)):
                raise e.ValueTypeViolation(f"{self._name}={value} expected array")
            if self._min_items is not None and not self.COMPARISONS["minItems"][
                "comparator"
            ](self._min_items)(value):
                raise self.COMPARISONS["minItems"]["errorClass"](
                    f"{self._name}={value} =/= minItems={self._min_items} constraint fails"
                )
            if self._max_items is not None and not self.COMPARISONS["maxItems"][
                "comparator"
            ](self._max_items)(value):
                raise self.COMPARISONS["maxItems"]["errorClass"](
                    f"{self._name}={value} =/= maxItems={self._max_items} constraint fails"
                )
            if self._unique_items is not None and not self.COMPARISONS["uniqueItems"][
                "comparator"
            ](self._unique_items)(value):
                raise self.COMPARISONS["uniqueItems"]["errorClass"](
                    f"{self._name}={value} =/= uniqueItems={self._unique_items} constraint fails"
                )
            if self._contains is not None:
                min_c = self._min_contains if self._min_contains is not None else 1
                if not self.COMPARISONS["minContains"]["comparator"](min_c)(
                    value, contains=self._contains
                ):
                    raise self.COMPARISONS["minContains"]["errorClass"](
                        f"{self._name}={value} =/= minContains={min_c} constraint fails"
                    )
                if self._max_contains is not None and not self.COMPARISONS[
                    "maxContains"
                ]["comparator"](self._max_contains)(value, contains=self._contains):
                    raise self.COMPARISONS["maxContains"]["errorClass"](
                        f"{self._name}={value} =/= maxContains={self._max_contains} constraint fails"
                    )
            if self._enum is not None and value not in self._enum:
                raise e.ValueTypeViolation(
                    f"{self._name}={value} =/= enum={self._raw_enum} constraint fails"
                )
            if self._has_subschemas:
                self._validate_subschemas(value)
        except e.SchemaViolation as exc:
            if errors is not None:
                errors.append(exc)
                if hasattr(obj, "__dict__"):
                    obj.__dict__[self._name] = value
                else:
                    self.__dict__[self._name] = value
                return
            raise

        if hasattr(obj, "__dict__"):
            obj.__dict__[self._name] = value
        else:
            self.__dict__[self._name] = value


class BooleanDescriptor(JSONSchemaFieldDescriptor[B]):
    COMPARISONS: ClassVar[dict] = {}

    def __init__(self, *, default=None, metadata=None) -> None:
        super().__init__(default=default, metadata=metadata or {})

    def __set__(self, obj, value):
        errors = (
            obj.__dict__.get("_validation_errors") if hasattr(obj, "__dict__") else None
        )
        try:
            if value is REQUIRED_MISSING:
                raise e.RequiredPropertyViolation(
                    f"{self._name} is a required property"
                )
            if type(value) is not bool and not isinstance(value, bool):
                raise e.ValueTypeViolation(f"{self._name}={value} expected boolean")
            if self._enum is not None and value not in self._enum:
                raise e.ValueTypeViolation(
                    f"{self._name}={value} =/= enum={self._raw_enum} constraint fails"
                )
            if self._has_subschemas:
                self._validate_subschemas(value)
        except e.SchemaViolation as exc:
            if errors is not None:
                errors.append(exc)
                if hasattr(obj, "__dict__"):
                    obj.__dict__[self._name] = value
                else:
                    self.__dict__[self._name] = value
                return
            raise

        if hasattr(obj, "__dict__"):
            obj.__dict__[self._name] = value
        else:
            self.__dict__[self._name] = value


class ObjectDescriptor(JSONSchemaFieldDescriptor[O]):
    COMPARISONS: ClassVar[dict] = {}

    def __init__(self, *, default=None, metadata=None) -> None:
        super().__init__(default=default, metadata=metadata or {})

    def __set__(self, obj, value):
        errors = (
            obj.__dict__.get("_validation_errors") if hasattr(obj, "__dict__") else None
        )
        try:
            if value is REQUIRED_MISSING:
                raise e.RequiredPropertyViolation(
                    f"{self._name} is a required property"
                )
            if not isinstance(value, dict):
                raise e.ValueTypeViolation(f"{self._name} expected object")
            if self._enum is not None and value not in self._enum:
                raise e.ValueTypeViolation(
                    f"{self._name}={value} =/= enum={self._raw_enum} constraint fails"
                )
            if self._has_subschemas:
                self._validate_subschemas(value)
        except e.SchemaViolation as exc:
            if errors is not None:
                errors.append(exc)
                if hasattr(obj, "__dict__"):
                    obj.__dict__[self._name] = value
                else:
                    self.__dict__[self._name] = value
                return
            raise

        if hasattr(obj, "__dict__"):
            obj.__dict__[self._name] = value
        else:
            self.__dict__[self._name] = value


class NullDescriptor(JSONSchemaFieldDescriptor[S]):
    COMPARISONS: ClassVar[dict] = {}

    def __init__(self, *, default=None, metadata=None) -> None:
        super().__init__(default=default, metadata=metadata or {})

    def __set__(self, obj, value):
        errors = (
            obj.__dict__.get("_validation_errors") if hasattr(obj, "__dict__") else None
        )
        try:
            if value is REQUIRED_MISSING:
                raise e.RequiredPropertyViolation(
                    f"{self._name} is a required property"
                )
            if value is not None:
                raise e.ValueTypeViolation(f"{self._name}={value} expected null")
            if self._enum is not None and value not in self._enum:
                raise e.ValueTypeViolation(
                    f"{self._name}={value} =/= enum={self._raw_enum} constraint fails"
                )
            if self._has_subschemas:
                self._validate_subschemas(value)
        except e.SchemaViolation as exc:
            if errors is not None:
                errors.append(exc)
                if hasattr(obj, "__dict__"):
                    obj.__dict__[self._name] = value
                else:
                    self.__dict__[self._name] = value
                return
            raise

        if hasattr(obj, "__dict__"):
            obj.__dict__[self._name] = value
        else:
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
        self._min_length = self._metadata.get("minLength")
        self._max_length = self._metadata.get("maxLength")

    def __set__(self, obj, value):  # noqa: C901
        errors = (
            obj.__dict__.get("_validation_errors") if hasattr(obj, "__dict__") else None
        )
        try:
            if value is REQUIRED_MISSING:
                raise e.RequiredPropertyViolation(
                    f"{self._name} is a required property"
                )
            if not isinstance(value, (list, tuple, set)):
                raise e.ValueTypeViolation(f"{self._name} expected collection")
            if self._min_length is not None and not self.COMPARISONS["minLength"][
                "comparator"
            ](self._min_length)(value):
                raise self.COMPARISONS["minLength"]["errorClass"](
                    f"{self._name}={value} =/= minLength={self._min_length} constraint fails"
                )
            if self._max_length is not None and not self.COMPARISONS["maxLength"][
                "comparator"
            ](self._max_length)(value):
                raise self.COMPARISONS["maxLength"]["errorClass"](
                    f"{self._name}={value} =/= maxLength={self._max_length} constraint fails"
                )
            if self._enum is not None and value not in self._enum:
                raise e.ValueTypeViolation(
                    f"{self._name}={value} =/= enum={self._raw_enum} constraint fails"
                )
            if self._has_subschemas:
                self._validate_subschemas(value)
        except e.SchemaViolation as exc:
            if errors is not None:
                errors.append(exc)
                if hasattr(obj, "__dict__"):
                    obj.__dict__[self._name] = value
                else:
                    self.__dict__[self._name] = value
                return
            raise

        if hasattr(obj, "__dict__"):
            obj.__dict__[self._name] = value
        else:
            self.__dict__[self._name] = value


class StringDescriptor(JSONSchemaFieldDescriptor[AnyStr]):
    COMPARISONS: ClassVar[dict] = {
        "maxLength": {
            "comparator": lambda d: partial(lambda bound, v: len(v) <= int(bound), d),
            "errorClass": e.LengthConstraintViolation,
        },
        "minLength": {
            "comparator": lambda d: partial(lambda bound, v: len(v) >= int(bound), d),
            "errorClass": e.LengthConstraintViolation,
        },
        "format": {
            "comparator": lambda d: partial(
                lambda bound, v: constants.STRING_FORMATS[bound](v), d
            ),
            "errorClass": e.StringFormatViolation,
        },
    }

    def __init__(self, *, default=None, metadata=None):
        super().__init__(default=default, metadata=metadata or {})
        self._min_length = self._metadata.get("minLength")
        self._max_length = self._metadata.get("maxLength")
        self._format = self._metadata.get("format")

    def __set__(self, obj, value):  # noqa: C901
        errors = (
            obj.__dict__.get("_validation_errors") if hasattr(obj, "__dict__") else None
        )
        try:
            if value is REQUIRED_MISSING:
                raise e.RequiredPropertyViolation(
                    f"{self._name} is a required property"
                )
            if type(value) is not str and not isinstance(value, (str, bytes)):
                raise e.ValueTypeViolation(f"{self._name}={value} expected string")
            if self._min_length is not None and not self.COMPARISONS["minLength"][
                "comparator"
            ](self._min_length)(value):
                raise self.COMPARISONS["minLength"]["errorClass"](
                    f"{self._name}={value} =/= minLength={self._min_length} constraint fails"
                )
            if self._max_length is not None and not self.COMPARISONS["maxLength"][
                "comparator"
            ](self._max_length)(value):
                raise self.COMPARISONS["maxLength"]["errorClass"](
                    f"{self._name}={value} =/= maxLength={self._max_length} constraint fails"
                )
            if self._format is not None and not self.COMPARISONS["format"][
                "comparator"
            ](self._format)(value):
                raise self.COMPARISONS["format"]["errorClass"](
                    f"{self._name}={value} =/= format={self._format} constraint fails"
                )
            if self._enum is not None and value not in self._enum:
                raise e.ValueTypeViolation(
                    f"{self._name}={value} =/= enum={self._raw_enum} constraint fails"
                )
            if self._has_subschemas:
                self._validate_subschemas(value)
        except e.SchemaViolation as exc:
            if errors is not None:
                errors.append(exc)
                if hasattr(obj, "__dict__"):
                    obj.__dict__[self._name] = value
                else:
                    self.__dict__[self._name] = value
                return
            raise

        if hasattr(obj, "__dict__"):
            obj.__dict__[self._name] = value
        else:
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
        self._minimum = self._metadata.get("minimum")
        self._maximum = self._metadata.get("maximum")
        self._exclusive_minimum = self._metadata.get("exclusiveMinimum")
        self._exclusive_maximum = self._metadata.get("exclusiveMaximum")
        self._multiple_of = self._metadata.get("multipleOf")

    def __set__(self, obj, value):  # noqa: C901
        errors = (
            obj.__dict__.get("_validation_errors") if hasattr(obj, "__dict__") else None
        )
        try:
            if value is REQUIRED_MISSING:
                raise e.RequiredPropertyViolation(
                    f"{self._name} is a required property"
                )
            if type(value) is bool or not isinstance(value, int):
                raise e.ValueTypeViolation(f"{self._name}={value} expected integer")
            if self._minimum is not None and not self.COMPARISONS["minimum"][
                "comparator"
            ](self._minimum)(value):
                raise self.COMPARISONS["minimum"]["errorClass"](
                    f"{self._name}={value} =/= minimum={self._minimum} constraint fails"
                )
            if self._maximum is not None and not self.COMPARISONS["maximum"][
                "comparator"
            ](self._maximum)(value):
                raise self.COMPARISONS["maximum"]["errorClass"](
                    f"{self._name}={value} =/= maximum={self._maximum} constraint fails"
                )
            if self._exclusive_minimum is not None and not self.COMPARISONS[
                "exclusiveMinimum"
            ]["comparator"](self._exclusive_minimum)(value):
                raise self.COMPARISONS["exclusiveMinimum"]["errorClass"](
                    f"{self._name}={value} =/= exclusiveMinimum={self._exclusive_minimum} constraint fails"
                )
            if self._exclusive_maximum is not None and not self.COMPARISONS[
                "exclusiveMaximum"
            ]["comparator"](self._exclusive_maximum)(value):
                raise self.COMPARISONS["exclusiveMaximum"]["errorClass"](
                    f"{self._name}={value} =/= exclusiveMaximum={self._exclusive_maximum} constraint fails"
                )
            if self._multiple_of is not None and not self.COMPARISONS["multipleOf"][
                "comparator"
            ](self._multiple_of)(value):
                raise self.COMPARISONS["multipleOf"]["errorClass"](
                    f"{self._name}={value} =/= multipleOf={self._multiple_of} constraint fails"
                )
            if self._enum is not None and value not in self._enum:
                raise e.ValueTypeViolation(
                    f"{self._name}={value} =/= enum={self._raw_enum} constraint fails"
                )
            if self._has_subschemas:
                self._validate_subschemas(value)
        except e.SchemaViolation as exc:
            if errors is not None:
                errors.append(exc)
                if hasattr(obj, "__dict__"):
                    obj.__dict__[self._name] = value
                else:
                    self.__dict__[self._name] = value
                return
            raise

        if hasattr(obj, "__dict__"):
            obj.__dict__[self._name] = value
        else:
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
        self._minimum = self._metadata.get("minimum")
        self._maximum = self._metadata.get("maximum")
        self._exclusive_minimum = self._metadata.get("exclusiveMinimum")
        self._exclusive_maximum = self._metadata.get("exclusiveMaximum")
        self._multiple_of = self._metadata.get("multipleOf")

    def __set__(self, obj, value):  # noqa: C901
        errors = (
            obj.__dict__.get("_validation_errors") if hasattr(obj, "__dict__") else None
        )
        try:
            if value is REQUIRED_MISSING:
                raise e.RequiredPropertyViolation(
                    f"{self._name} is a required property"
                )
            if type(value) is bool or not isinstance(value, (int, float)):
                raise e.ValueTypeViolation(f"{self._name}={value} expected number")
            if self._minimum is not None and not self.COMPARISONS["minimum"][
                "comparator"
            ](self._minimum)(value):
                raise self.COMPARISONS["minimum"]["errorClass"](
                    f"{self._name}={value} =/= minimum={self._minimum} constraint fails"
                )
            if self._maximum is not None and not self.COMPARISONS["maximum"][
                "comparator"
            ](self._maximum)(value):
                raise self.COMPARISONS["maximum"]["errorClass"](
                    f"{self._name}={value} =/= maximum={self._maximum} constraint fails"
                )
            if self._exclusive_minimum is not None and not self.COMPARISONS[
                "exclusiveMinimum"
            ]["comparator"](self._exclusive_minimum)(value):
                raise self.COMPARISONS["exclusiveMinimum"]["errorClass"](
                    f"{self._name}={value} =/= exclusiveMinimum={self._exclusive_minimum} constraint fails"
                )
            if self._exclusive_maximum is not None and not self.COMPARISONS[
                "exclusiveMaximum"
            ]["comparator"](self._exclusive_maximum)(value):
                raise self.COMPARISONS["exclusiveMaximum"]["errorClass"](
                    f"{self._name}={value} =/= exclusiveMaximum={self._exclusive_maximum} constraint fails"
                )
            if self._multiple_of is not None and not self.COMPARISONS["multipleOf"][
                "comparator"
            ](self._multiple_of)(value):
                raise self.COMPARISONS["multipleOf"]["errorClass"](
                    f"{self._name}={value} =/= multipleOf={self._multiple_of} constraint fails"
                )
            if self._enum is not None and value not in self._enum:
                raise e.ValueTypeViolation(
                    f"{self._name}={value} =/= enum={self._raw_enum} constraint fails"
                )
            if self._has_subschemas:
                self._validate_subschemas(value)
        except e.SchemaViolation as exc:
            if errors is not None:
                errors.append(exc)
                if hasattr(obj, "__dict__"):
                    obj.__dict__[self._name] = value
                else:
                    self.__dict__[self._name] = value
                return
            raise

        if hasattr(obj, "__dict__"):
            obj.__dict__[self._name] = value
        else:
            self.__dict__[self._name] = value


class SpecialKeywordDescriptor(JSONSchemaFieldDescriptor[A]):
    COMPARISONS: ClassVar[dict] = {}
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
