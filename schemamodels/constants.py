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
from schemamodels.utils import ifraises, raise_on_none

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
        m.group(2) if (m := URI_CHECK_PATTERN.match(e)) else None,
        exceptions.StringFormatViolation,
    ),
}
