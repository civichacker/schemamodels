# SPDX-FileCopyrightText: 2023-2026 Civic Hacker LLC
# SPDX-License-Identifier: GPL-3.0-or-later

from re import sub
from typing import TypeVar

T = TypeVar("T")


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


def reraises(reraise_exception, exception_class=ValueError):
    raise reraise_exception()
