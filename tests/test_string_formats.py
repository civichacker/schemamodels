# SPDX-FileCopyrightText: 2023-2026 Civic Hacker LLC
# SPDX-License-Identifier: GPL-3.0-or-later

import importlib
import json

import pytest

from schemamodels import exceptions


@pytest.mark.string
@pytest.mark.format
@pytest.mark.email
def test_string_email_format_support(Factory):
    schemadoc = """
    {
        "title": "email-format",
        "description": "Blue Blah",
        "type": "object",
        "properties": {
            "user_email": {
              "type": "string",
              "format": "email"
            }
        }
    }
    """
    stringformat = json.loads(schemadoc)
    importlib.import_module("schemamodels.dynamic")
    sm = Factory()
    sm.register(stringformat)

    from schemamodels.dynamic import EmailFormat

    EmailFormat(user_email="test@examplemail.co")
    with pytest.raises(exceptions.StringFormatViolation):
        EmailFormat(user_email="abcdefgh")


@pytest.mark.string
@pytest.mark.format
def test_string_datetime_format_support(Factory):
    schemadoc = """
    {
        "title": "date-time-format",
        "description": "Blue Blah",
        "type": "object",
        "properties": {
            "event_time": {
              "type": "string",
              "format": "date-time"
            }
        }
    }
    """
    stringformat = json.loads(schemadoc)
    sm = Factory()
    sm.register(stringformat)

    from schemamodels.dynamic import DateTimeFormat

    DateTimeFormat(event_time="2018-11-13T20:20:39+00:00")
    with pytest.raises(exceptions.StringFormatViolation):
        DateTimeFormat(event_time="abcdefgh")


@pytest.mark.string
@pytest.mark.format
def test_string_date_format_support(Factory):
    schemadoc = """
    {
        "title": "date-format",
        "description": "Blue Blah",
        "type": "object",
        "properties": {
            "event_time": {
              "type": "string",
              "format": "date-time"
            }
        }
    }
    """
    stringformat = json.loads(schemadoc)
    sm = Factory()
    sm.register(stringformat)

    from schemamodels.dynamic import DateFormat

    DateFormat(event_time="2018-11-13")
    DateFormat(event_time="20181113")
    with pytest.raises(exceptions.StringFormatViolation):
        DateFormat(event_time="Nov 13, 2018")
        DateFormat(event_time="November 13, 2018")
        DateFormat(event_time="abcdefgh")


@pytest.mark.string
@pytest.mark.format
def test_string_time_format_support(Factory):
    schemadoc = """
    {
        "title": "time-format",
        "description": "Blue Blah",
        "type": "object",
        "properties": {
            "event_time": {
              "type": "string",
              "format": "time"
            }
        }
    }
    """
    stringformat = json.loads(schemadoc)
    sm = Factory()
    sm.register(stringformat)

    from schemamodels.dynamic import TimeFormat

    TimeFormat(event_time="23:20:00")
    with pytest.raises(exceptions.StringFormatViolation):
        TimeFormat(event_time="27:20:00")
        TimeFormat(event_time="2023-12-02")
        TimeFormat(event_time="abcdefgh")


@pytest.mark.string
@pytest.mark.format
def test_string_ipaddress_format_support(Factory):
    schemadoc = """
    {
        "title": "internet-format",
        "description": "Blue Blah",
        "type": "object",
        "properties": {
            "event_location": {
              "type": "string",
              "format": "ipv4"
            }
        }
    }
    """
    stringformat = json.loads(schemadoc)
    sm = Factory()
    sm.register(stringformat)

    from schemamodels.dynamic import InternetFormat

    InternetFormat(event_location="127.0.0.1")
    with pytest.raises(exceptions.StringFormatViolation):
        InternetFormat(event_location="welpwelp")


@pytest.mark.string
@pytest.mark.format
def test_string_hostname_format_support(Factory):
    schemadoc = """
    {
        "title": "internet-format",
        "description": "Blue Blah",
        "type": "object",
        "properties": {
            "webhost": {
              "type": "string",
              "format": "hostname"
            }
        }
    }
    """
    stringformat = json.loads(schemadoc)
    sm = Factory()
    sm.register(stringformat)

    from schemamodels.dynamic import InternetFormat

    InternetFormat(webhost="git+https://qwdqwdwd.com")
    InternetFormat(webhost="http://example.com")
    InternetFormat(webhost="https://sub.domain-name.org")
    InternetFormat(webhost="coap+tcp://example.com")
    InternetFormat(webhost="custom-1.scheme://example.com")
    InternetFormat(webhost="example.com")
    with pytest.raises(exceptions.StringFormatViolation):
        InternetFormat(webhost="qwdqwd//qwdqwdwd.com")
        InternetFormat(webhost="127.0.0.1")


@pytest.mark.string
@pytest.mark.format
def test_string_uri_format_support(Factory):
    schemadoc = """
    {
        "title": "internet-format",
        "description": "Blue Blah",
        "type": "object",
        "properties": {
            "resource_uri": {
              "type": "string",
              "format": "uri"
            }
        }
    }
    """
    stringformat = json.loads(schemadoc)
    sm = Factory()
    sm.register(stringformat)

    from schemamodels.dynamic import InternetFormat

    InternetFormat(resource_uri="ftp://ftp.is.co.za/rfc/rfc1808.txt")
    InternetFormat(resource_uri="http://www.ietf.org/rfc/rfc2396.txt")
    InternetFormat(resource_uri="ldap://[2001:db8::7]/c=GB?objectClass?one")
    InternetFormat(resource_uri="mailto:John.Doe@example.com")
    InternetFormat(resource_uri="news:comp.infosystems.www.servers.unix")
    InternetFormat(resource_uri="tel:+1-816-555-1212")
    InternetFormat(resource_uri="telnet://192.0.2.16:80/")
    InternetFormat(
        resource_uri="urn:oasis:names:specification:docbook:dtd:xml:4.1.2"
    )
    with pytest.raises(exceptions.StringFormatViolation):
        InternetFormat(resource_uri="abcdefgh")
