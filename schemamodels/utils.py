# SPDX-FileCopyrightText: 2023-2026 Civic Hacker LLC
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
from re import sub
from typing import Any, TypeVar

T = TypeVar("T")


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
    if "minimum" in subschema and isinstance(value, (int, float)) and type(value) is not bool and not (value >= subschema["minimum"]):
        return False
    if "maximum" in subschema and isinstance(value, (int, float)) and type(value) is not bool and not (value <= subschema["maximum"]):
        return False
    if "exclusiveMinimum" in subschema and isinstance(value, (int, float)) and type(value) is not bool and not (value > subschema["exclusiveMinimum"]):
        return False
    if "exclusiveMaximum" in subschema and isinstance(value, (int, float)) and type(value) is not bool and not (value < subschema["exclusiveMaximum"]):
        return False
    if "multipleOf" in subschema and isinstance(value, (int, float)) and type(value) is not bool and value % subschema["multipleOf"] != 0:
        return False
    if "maxLength" in subschema and isinstance(value, str) and not (len(value) <= subschema["maxLength"]):
        return False
    if "minLength" in subschema and isinstance(value, str) and not (len(value) >= subschema["minLength"]):
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


def generate_classname(title: str) -> str:
    return sub(r"(-|_)+", "", title.title())


def is_schema_toplevel_object(schema: dict) -> bool:
    reqkws = {"title", "type", "properties"}
    return not (not reqkws <= schema.keys() or schema.get("type", None) != "object")


def ifraises(func, value, reraise_exception, exception_class=ValueError):
    try:
        func(value)
    except exception_class:
        tb = sys.exception().__traceback__
        raise reraise_exception().with_traceback(tb)
    return True


def raise_on_none(expression, exception_class):
    if not expression:
        raise exception_class()
    return True
