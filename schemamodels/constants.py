# SPDX-FileCopyrightText: 2023-2026 Civic Hacker LLC
# SPDX-License-Identifier: GPL-3.0-or-later
import email.headerregistry
import ipaddress
import re
from datetime import date, datetime, time
from functools import partial
from operator import contains, ge, gt, le, lt, mod, not_
from urllib.parse import urlparse

from schemamodels import exceptions
from schemamodels.utils import (
    _are_items_unique,
    ifraises,
    raise_on_none,
    validate_subschema,
)

REQUIRED_MISSING = object()

#  https://www.rfc-editor.org/info/rfc3986/#section-3.1
SCHEME_CHECK_PATTERN = re.compile(r"^[a-z][a-z0-9+.-]*(?=://)", flags=re.IGNORECASE)
HOSTNAME_PATTERN = re.compile(
    r"^(?!-)[a-z0-9-]{1,63}(?<!-)(\.(?!-)[a-z0-9-]{1,63}(?<!-))*$",
    re.IGNORECASE,
)
#  https://www.rfc-editor.org/info/rfc3986/#appendix-B
URI_CHECK_PATTERN = re.compile(
    r"^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?"
)
URI_SCHEME_PATTERN = re.compile(r"^[a-z][a-z0-9+.-]*$", flags=re.IGNORECASE)
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    flags=re.IGNORECASE,
)
# https://www.rfc-editor.org/info/rfc3339/#appendix-A
DURATION_PATTERN = re.compile(
    r"^P([0-9]+W|T([0-9]+H([0-9]+M([0-9]+S)?)?|[0-9]+M([0-9]+S)?|[0-9]+S)|([0-9]+D|[0-9]+M([0-9]+D)?|[0-9]+Y([0-9]+M([0-9]+D)?)?)(T([0-9]+H([0-9]+M([0-9]+S)?)?|[0-9]+M([0-9]+S)?|[0-9]+S))?)$"
)

DEFAULT_FACTORIES = {
    "string": str,
    "integer": int,
    "number": float,
    "null": None,
    "boolean": bool,
    "not": callable,
    "anyof": callable,
    "allof": callable,
    "array": list,
    "object": dict,
}

JSON_TYPE_MAP = {
    "string": lambda d: isinstance(d, str),
    "object": lambda d: isinstance(d, dict),
    "integer": lambda d: isinstance(d, int),
    "number": lambda d: isinstance(d, (float, int)),
    "null": lambda d: d is None,
    "boolean": lambda d: isinstance(d, bool),
    "array": lambda d: isinstance(d, (list, tuple)),
}

PORCELINE_KEYWORDS = [
    "value",
    "default",
    "anyOf",
    "allOf",
    "oneOf",
    "not",
    "description",
]


COMPARISONS = {
    "type": lambda d: JSON_TYPE_MAP[d],
    "not": lambda d: not_(d),
    "minimum": lambda d: partial(le, d),
    "maximum": lambda d: partial(ge, d),
    "exclusiveMinimum": lambda d: partial(lt, d),
    "exclusiveMaximum": lambda d: partial(gt, d),
    "enum": lambda d: partial(contains, d),
    "format": lambda d: partial(lambda bound, v: STRING_FORMATS[bound](v), d),
    "maxLength": lambda d: partial(lambda bound, v: len(v) <= bound, d),
    "minLength": lambda d: partial(lambda bound, v: len(v) >= bound, d),
    "multipleOf": lambda d: partial(lambda d, n: mod(n, d) == 0, d),
    "maxItems": lambda d: partial(
        lambda bound, v: 0 <= len(v) <= bound if isinstance(v, (list, tuple)) else True,
        d,
    ),
    "minItems": lambda d: partial(
        lambda bound, v: 0 <= bound <= len(v) if isinstance(v, (list, tuple)) else True,
        d,
    ),
    "uniqueItems": lambda d: partial(
        lambda unique, v: (
            (_are_items_unique(v) if unique else True)
            if isinstance(v, (list, tuple))
            else True
        ),
        d,
    ),
    "contains": lambda d: partial(
        lambda subschema, v: (
            any(validate_subschema(subschema, item) for item in v)
            if isinstance(v, (list, tuple))
            else True
        ),
        d,
    ),
    "minContains": lambda d: lambda v: True,
    "maxContains": lambda d: lambda v: True,
}

STRING_FORMATS = {
    "email": lambda e: ifraises(
        partial(email.headerregistry.Address, addr_spec=e),
        e,
        exceptions.StringFormatViolation,
        exception_class=ValueError,
    ),
    "date-time": lambda e: ifraises(
        datetime.fromisoformat,
        e,
        exceptions.StringFormatViolation,
        exception_class=ValueError,
    ),
    "date": lambda e: ifraises(
        date.fromisoformat,
        e,
        exceptions.StringFormatViolation,
        exception_class=ValueError,
    ),
    "time": lambda e: ifraises(
        time.fromisoformat,
        e,
        exceptions.StringFormatViolation,
        exception_class=ValueError,
    ),
    "ipv4": lambda e: ifraises(
        ipaddress.IPv4Address,
        e,
        exceptions.StringFormatViolation,
        exception_class=ipaddress.AddressValueError,
    ),
    "ipv6": lambda e: ifraises(
        ipaddress.IPv6Address,
        e,
        exceptions.StringFormatViolation,
        exception_class=ipaddress.AddressValueError,
    ),
    "hostname": lambda e: raise_on_none(
        host
        if (
            host := (
                urlparse(e).hostname
                if SCHEME_CHECK_PATTERN.match(e)
                else urlparse(f"//{e}").hostname
            )
        )
        and len(host) <= 253
        and HOSTNAME_PATTERN.match(host)
        and not host.split(".")[-1].isdigit()
        else None,
        exceptions.StringFormatViolation,
    ),
    "uri": lambda e: raise_on_none(
        m.group(2)
        if isinstance(e, str)
        and e.isascii()
        and not re.search(r"[\s<>\"\\^`{|}]", e)
        and (m := URI_CHECK_PATTERN.match(e))
        and m.group(2)
        and URI_SCHEME_PATTERN.match(m.group(2))
        else None,
        exceptions.StringFormatViolation,
    ),
    "uri-reference": lambda e: raise_on_none(
        True
        if isinstance(e, str)
        and e.isascii()
        and not re.search(r"[\s<>\"\\^`{|}]", e)
        and (m := URI_CHECK_PATTERN.match(e))
        and (m.group(2) is None or URI_SCHEME_PATTERN.match(m.group(2)))
        else None,
        exceptions.StringFormatViolation,
    ),
    "iri": lambda e: raise_on_none(
        m.group(2)
        if isinstance(e, str)
        and not re.search(r"[\s<>\"\\^`{|}]", e)
        and (m := URI_CHECK_PATTERN.match(e))
        and m.group(2)
        and URI_SCHEME_PATTERN.match(m.group(2))
        else None,
        exceptions.StringFormatViolation,
    ),
    "iri-reference": lambda e: raise_on_none(
        True
        if isinstance(e, str)
        and not re.search(r"[\s<>\"\\^`{|}]", e)
        and (m := URI_CHECK_PATTERN.match(e))
        and (m.group(2) is None or URI_SCHEME_PATTERN.match(m.group(2)))
        else None,
        exceptions.StringFormatViolation,
    ),
    "uuid": lambda e: raise_on_none(
        isinstance(e, str) and UUID_PATTERN.match(e),
        exceptions.StringFormatViolation,
    ),
    "duration": lambda e: raise_on_none(
        isinstance(e, str) and DURATION_PATTERN.match(e),
        exceptions.StringFormatViolation,
    ),
}
