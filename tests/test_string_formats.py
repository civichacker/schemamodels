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
    InternetFormat(
        resource_uri="urn:uuid:f81d4fae-7dec-11d0-a765-00a0c91e6bf6"
    )
    with pytest.raises(exceptions.StringFormatViolation):
        InternetFormat(resource_uri="abcdefgh")
        InternetFormat(resource_uri="//example.com/relative")
        InternetFormat(resource_uri="/path/to/resource")
        InternetFormat(resource_uri="http://example.com/invalid path")
        InternetFormat(resource_uri="https://例え.テスト/メイン")


@pytest.mark.string
@pytest.mark.format
def test_string_uri_reference_format_support(Factory):
    schemadoc = """
    {
        "title": "uri-reference-format",
        "description": "URI Reference format validation per RFC 3986 section 4.1",
        "type": "object",
        "properties": {
            "resource_ref": {
              "type": "string",
              "format": "uri-reference"
            }
        }
    }
    """
    stringformat = json.loads(schemadoc)
    sm = Factory()
    sm.register(stringformat)

    from schemamodels.dynamic import UriReferenceFormat

    # Full URIs are valid URI references (RFC 3986 section 4.1: URI-reference = URI / relative-ref)
    UriReferenceFormat(resource_ref="ftp://ftp.is.co.za/rfc/rfc1808.txt")
    UriReferenceFormat(resource_ref="http://www.ietf.org/rfc/rfc2396.txt")
    UriReferenceFormat(
        resource_ref="ldap://[2001:db8::7]/c=GB?objectClass?one"
    )
    UriReferenceFormat(resource_ref="mailto:John.Doe@example.com")
    UriReferenceFormat(
        resource_ref="urn:oasis:names:specification:docbook:dtd:xml:4.1.2"
    )
    # Relative references per RFC 3986 section 4.2
    UriReferenceFormat(resource_ref="//example.com/foo")
    UriReferenceFormat(resource_ref="/path/to/resource")
    UriReferenceFormat(resource_ref="foo/bar")
    UriReferenceFormat(resource_ref="./foo/bar")
    UriReferenceFormat(resource_ref="../relative/path")
    UriReferenceFormat(resource_ref="?query=test")
    UriReferenceFormat(resource_ref="#section-1")
    UriReferenceFormat(resource_ref="f81d4fae-7dec-11d0-a765-00a0c91e6bf6")
    UriReferenceFormat(resource_ref="")

    with pytest.raises(exceptions.StringFormatViolation):
        UriReferenceFormat(resource_ref="http://example.com/invalid path")
        UriReferenceFormat(resource_ref="path with spaces/resource")
        UriReferenceFormat(resource_ref="https://例え.テスト/メイン")


@pytest.mark.string
@pytest.mark.format
def test_string_iri_format_support(Factory):
    schemadoc = """
    {
        "title": "iri-format",
        "description": "IRI format validation per RFC 3987",
        "type": "object",
        "properties": {
            "resource_iri": {
              "type": "string",
              "format": "iri"
            }
        }
    }
    """
    stringformat = json.loads(schemadoc)
    sm = Factory()
    sm.register(stringformat)

    from schemamodels.dynamic import IriFormat

    # Note: all valid URIs are valid IRIs
    IriFormat(resource_iri="ftp://ftp.is.co.za/rfc/rfc1808.txt")
    IriFormat(resource_iri="http://www.ietf.org/rfc/rfc2396.txt")
    IriFormat(resource_iri="ldap://[2001:db8::7]/c=GB?objectClass?one")
    IriFormat(resource_iri="mailto:John.Doe@example.com")
    IriFormat(resource_iri="news:comp.infosystems.www.servers.unix")
    IriFormat(resource_iri="tel:+1-816-555-1212")
    IriFormat(resource_iri="telnet://192.0.2.16:80/")
    IriFormat(
        resource_iri="urn:oasis:names:specification:docbook:dtd:xml:4.1.2"
    )
    IriFormat(resource_iri="urn:uuid:f81d4fae-7dec-11d0-a765-00a0c91e6bf6")
    # Internationalized Resource Identifiers with Unicode / UCS characters
    IriFormat(resource_iri="https://en.wiktionary.org/wiki/Ῥόδος")
    IriFormat(resource_iri="http://例え.テスト/メイン")
    IriFormat(resource_iri="http://example.com/résumé")
    IriFormat(resource_iri="https://日本語.jp/パス")

    with pytest.raises(exceptions.StringFormatViolation):
        IriFormat(resource_iri="abcdefgh")
        IriFormat(resource_iri="/relative/path")
        IriFormat(resource_iri="//example.com/foo")
        IriFormat(resource_iri="http://example.com/invalid path with spaces")


@pytest.mark.string
@pytest.mark.format
def test_string_iri_reference_format_support(Factory):
    schemadoc = """
    {
        "title": "iri-reference-format",
        "description": "IRI Reference format validation per RFC 3987",
        "type": "object",
        "properties": {
            "resource_ref": {
              "type": "string",
              "format": "iri-reference"
            }
        }
    }
    """
    stringformat = json.loads(schemadoc)
    sm = Factory()
    sm.register(stringformat)

    from schemamodels.dynamic import IriReferenceFormat

    # Note: all valid URIs and valid URI References are also valid IRI References
    IriReferenceFormat(resource_ref="http://www.ietf.org/rfc/rfc2396.txt")
    IriReferenceFormat(resource_ref="mailto:John.Doe@example.com")
    IriReferenceFormat(
        resource_ref="urn:oasis:names:specification:docbook:dtd:xml:4.1.2"
    )
    IriReferenceFormat(resource_ref="//example.com/foo")
    IriReferenceFormat(resource_ref="/path/to/resource")
    IriReferenceFormat(resource_ref="foo/bar")
    IriReferenceFormat(resource_ref="./foo/bar")
    IriReferenceFormat(resource_ref="../relative/path")
    IriReferenceFormat(resource_ref="?query=test")
    IriReferenceFormat(resource_ref="#section-1")
    IriReferenceFormat(resource_ref="")
    # Internationalized IRIs and relative IRI references
    IriReferenceFormat(resource_ref="https://en.wiktionary.org/wiki/Ῥόδος")
    IriReferenceFormat(resource_ref="http://例え.テスト/メイン")
    IriReferenceFormat(resource_ref="http://example.com/résumé")
    IriReferenceFormat(resource_ref="/パス/ファイル")
    IriReferenceFormat(resource_ref="../résumé#セクション")
    IriReferenceFormat(resource_ref="例え")
    IriReferenceFormat(resource_ref="?検索=テスト")
    IriReferenceFormat(resource_ref="#フラグメント")

    with pytest.raises(exceptions.StringFormatViolation):
        IriReferenceFormat(resource_ref="http://example.com/invalid path with spaces")
        IriReferenceFormat(resource_ref="/invalid path/with spaces")


@pytest.mark.string
@pytest.mark.format
def test_string_uuid_format_support(Factory):
    schemadoc = """
    {
        "title": "uuid-format",
        "description": "UUID format validation per RFC 4122",
        "type": "object",
        "properties": {
            "resource_uuid": {
              "type": "string",
              "format": "uuid"
            }
        }
    }
    """
    stringformat = json.loads(schemadoc)
    sm = Factory()
    sm.register(stringformat)

    from schemamodels.dynamic import UuidFormat

    # Plain UUIDs per RFC 4122
    UuidFormat(resource_uuid="f81d4fae-7dec-11d0-a765-00a0c91e6bf6")
    UuidFormat(resource_uuid="123e4567-e89b-12d3-a456-426614174000")
    UuidFormat(resource_uuid="00000000-0000-0000-0000-000000000000")
    UuidFormat(resource_uuid="C971844B-8343-4C70-9883-7E0D3643C88F")

    # UUIDs in URNs and malformed UUID strings must fail
    with pytest.raises(exceptions.StringFormatViolation):
        UuidFormat(
            resource_uuid="urn:uuid:f81d4fae-7dec-11d0-a765-00a0c91e6bf6"
        )
        UuidFormat(resource_uuid="f81d4fae7dec11d0a76500a0c91e6bf6")
        UuidFormat(resource_uuid="f81d4fae-7dec-11d0-a765-00a0c91e6bfg")
        UuidFormat(resource_uuid="f81d4fae-7dec-11d0-a765")
        UuidFormat(resource_uuid="abcdefgh")


@pytest.mark.string
@pytest.mark.format
def test_string_duration_format_support(Factory):
    schemadoc = """
    {
        "title": "duration-format",
        "description": "Duration format validation per RFC 3339 Appendix A / ISO 8601",
        "type": "object",
        "properties": {
            "time_duration": {
              "type": "string",
              "format": "duration"
            }
        }
    }
    """
    stringformat = json.loads(schemadoc)
    sm = Factory()
    sm.register(stringformat)

    from schemamodels.dynamic import DurationFormat

    # Valid Durations per RFC 3339 Appendix A:
    # 1. Date durations (years, months, days)
    DurationFormat(time_duration="P3Y")
    DurationFormat(time_duration="P2M")
    DurationFormat(time_duration="P4D")
    DurationFormat(time_duration="P1Y2M")
    DurationFormat(time_duration="P1Y2M3D")
    DurationFormat(time_duration="P2M3D")
    DurationFormat(time_duration="P100Y10M20D")

    # 2. Week durations
    DurationFormat(time_duration="P1W")
    DurationFormat(time_duration="P4W")
    DurationFormat(time_duration="P52W")

    # 3. Time durations (hours, minutes, seconds)
    DurationFormat(time_duration="PT12H")
    DurationFormat(time_duration="PT30M")
    DurationFormat(time_duration="PT5S")
    DurationFormat(time_duration="PT12H30M")
    DurationFormat(time_duration="PT12H30M5S")
    DurationFormat(time_duration="PT30M5S")

    # 4. Combined Date and Time durations
    DurationFormat(time_duration="P3Y6M4DT12H30M5S")
    DurationFormat(time_duration="P1YT1H")
    DurationFormat(time_duration="P2MT2M")
    DurationFormat(time_duration="P3DT3S")
    DurationFormat(time_duration="P1Y2MT1H2M")
    DurationFormat(time_duration="P2M3DT4H5M6S")
    DurationFormat(time_duration="P1Y2M3DT1H")
    DurationFormat(time_duration="P1Y2M3DT1M")
    DurationFormat(time_duration="P1Y2M3DT1S")

    # Invalid Durations
    invalid_durations = [
        "",
        "P",
        "PT",
        "P1",
        "PT1",
        "1Y",
        "T1H",
        "P1Y1D",  # Day cannot follow year directly without month
        "P3Y4D",
        "PT1H1S",  # Second cannot follow hour directly without minute
        "PT12H5S",
        "P1W1D",  # Week cannot be combined with day
        "P1WT1H",  # Week cannot be combined with time
        "P1Y2W",  # Week cannot follow year
        "P1Y2M3D4W",
        "P-1Y",  # Negative numbers not permitted
        "P1.5Y",  # Fractional numbers not permitted
        "P1,5Y",
        "p1y",  # Lowercase not permitted
        "pt1h",
        "P1H",  # Time units require "T" prefix
        "P1S",
        "P1H2M",
        "P1M1Y",  # Wrong order
        "P1D1M",
        "PT1M1H",
        "PT1S1M",
        "abcdefgh",
        "2020-01-01",
        "P1Y ",
        " P1Y",
    ]

    for invalid in invalid_durations:
        with pytest.raises(exceptions.StringFormatViolation):
            DurationFormat(time_duration=invalid)
