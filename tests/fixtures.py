import json
import pytest


@pytest.fixture
def simple_schema():
    test = '''
    {
        "$id": "https://schema.dev/fake-schema.schema.json",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "simple-schema",
        "description": "",
        "type": "object",
        "properties": {
            "provider_id": {
              "description": "this is a description",
              "type": "integer"
            },
            "brand_name": {
              "type": "string"
            }
        }
    }
    '''
    yield json.loads(test)


@pytest.fixture
def malformed_schema():
    test = '''
    {
        "$id": "https://schema.dev/fake-schema.schema.json",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "description": "",
        "title": "malformed-object",
        "type": "object"
    }
    '''
    yield json.loads(test)


@pytest.fixture
def required_fields_schema():
    test = '''
    {
        "$id": "https://schema.dev/fake-schema.schema.json",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "required-schema",
        "description": "",
        "type": "object",
        "properties": {
            "provider_id": {
              "description": "this is a description",
              "type": "integer"
            },
            "brand_name": {
              "type": "string"
            }
        },
        "required": ["brand_name"]
    }
    '''

    yield json.loads(test)


@pytest.fixture
def default_value_schema():
    test = '''
    {
        "$id": "https://schema.dev/fake-schema.schema.json",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "default-schema",
        "description": "Blue Blah",
        "type": "object",
        "properties": {
            "provider_id": {
              "description": "this is a description",
              "default": 5,
              "type": "integer"
            },
            "brand_name": {
              "type": "string"
            }
        }
    }
    '''
    yield json.loads(test)


@pytest.fixture
def enum_field_schema():
    enum = '''
    {
        "$id": "https://schema.dev/fake-schema.schema.json",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "enum-schema",
        "description": "Blue Blah",
        "type": "object",
        "properties": {
            "handiness": {
                "description": "this is a description",
                "enum": ["left", "right", "all", "none"],
                "type": "string"
            },
            "brand_name": {
                "description": "this is a description",
                "type": "string"
            }
        }
    }
    '''
    yield json.loads(enum)
