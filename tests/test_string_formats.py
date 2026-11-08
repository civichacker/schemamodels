import json
import pytest
import importlib
from schemamodels import exceptions

@pytest.mark.string
@pytest.mark.format
def test_string_email_format_support(Factory):
    schemadoc = '''
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
    '''
    stringformat = json.loads(schemadoc)
    importlib.import_module("schemamodels.dynamic")
    sm = Factory()
    sm.register(stringformat)

    from schemamodels.dynamic import EmailFormat

    fs = EmailFormat(user_email="test@examplemail.co")
    with pytest.raises(exceptions.StringFormatViolation):
        fs = EmailFormat(user_email="abcdefgh")


@pytest.mark.string
@pytest.mark.format
def test_string_datetime_format_support(Factory):
    schemadoc = '''
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
    '''
    stringformat = json.loads(schemadoc)
    sm = Factory()
    sm.register(stringformat)

    from schemamodels.dynamic import DateTimeFormat


    fs = DateTimeFormat(event_time="2018-11-13T20:20:39+00:00")
    with pytest.raises(exceptions.StringFormatViolation):
        fs = DateTimeFormat(event_time="abcdefgh")


@pytest.mark.string
@pytest.mark.format
def test_string_date_format_support(Factory):
    schemadoc = '''
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
    '''
    stringformat = json.loads(schemadoc)
    sm = Factory()
    sm.register(stringformat)

    from schemamodels.dynamic import DateFormat


    fs = DateFormat(event_time="2018-11-13")
    fs = DateFormat(event_time="20181113")
    with pytest.raises(exceptions.StringFormatViolation):
        fs = DateFormat(event_time="Nov 13, 2018")
        fs = DateFormat(event_time="November 13, 2018")
        fs = DateFormat(event_time="abcdefgh")


@pytest.mark.string
@pytest.mark.format
def test_string_time_format_support(Factory):
    schemadoc = '''
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
    '''
    stringformat = json.loads(schemadoc)
    sm = Factory()
    sm.register(stringformat)

    from schemamodels.dynamic import TimeFormat


    fs = TimeFormat(event_time="23:20:00")
    with pytest.raises(exceptions.StringFormatViolation):
        fs = TimeFormat(event_time="27:20:00")
        fs = TimeFormat(event_time="2023-12-02")
        fs = TimeFormat(event_time="abcdefgh")






@pytest.mark.string
@pytest.mark.format
def test_string_ipaddress_format_support(Factory):
    schemadoc = '''
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
    '''
    stringformat = json.loads(schemadoc)
    sm = Factory()
    sm.register(stringformat)

    from schemamodels.dynamic import InternetFormat

    fs = InternetFormat(event_location='127.0.0.1')
    with pytest.raises(exceptions.StringFormatViolation):
        fs = InternetFormat(event_location='welpwelp')


@pytest.mark.string
@pytest.mark.format
def test_string_hostname_format_support(Factory):
    schemadoc = '''
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
    '''
    stringformat = json.loads(schemadoc)
    sm = Factory()
    sm.register(stringformat)

    from schemamodels.dynamic import InternetFormat

    fs = InternetFormat(webhost='127.0.0.1')
    with pytest.raises(exceptions.StringFormatViolation):
        fs = InternetFormat(webhost='qwdqwd//qwdqwdwd.com')