from jsonschema import validators, protocols, validate
import json
import importlib
from dataclasses import make_dataclass, FrozenInstanceError, asdict

from schemamodels import SchemaModelFactory

import pytest

def test_enforce_required():
    test = '''
    {
        "$id": "https://schema.dev/fake-schema.schema.json",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "fake-schema",
        "description": "",
        "type": "object",
        "properties": {
            "provider_id": {
              "type": "integer"
            },
            "brand_name": {
              "type": "string"
            }
        },
        "required": ["brand_name"]
    }
    '''
    t = json.loads(test)
    dmod = importlib.import_module('schemamodels.dynamic')
    sm = SchemaModelFactory()
    validators.Draft202012Validator.check_schema(t)

    try:
        assert sm.register(t)
        from schemamodels.dynamic import FakeSchema
    except Exception:
        assert False

    with pytest.raises(TypeError):
        FakeSchema()
        FakeSchema(provider_id=1)


def test_immutability():
    test = '''
    {
        "$id": "https://schema.dev/fake-schema.schema.json",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "fake-schema",
        "description": "Blue Blah",
        "type": "object",
        "properties": {
            "provider_id": {
              "type": "integer"
            },
            "brand_name": {
              "type": "string"
            }
        }
    }
    '''
    t = json.loads(test)
    sm = SchemaModelFactory()
    sm.register(t)

    from schemamodels.dynamic import FakeSchema
    fs = FakeSchema(provider_id=1, brand_name="yo")

    with pytest.raises(FrozenInstanceError):
        fs.provider_id = 3


def test_default_support():
    test = '''
    {
        "$id": "https://schema.dev/fake-schema.schema.json",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "fake-schema",
        "description": "Blue Blah",
        "type": "object",
        "properties": {
            "provider_id": {
              "default": 5,
              "type": "integer"
            },
            "brand_name": {
              "type": "string"
            }
        }
    }
    '''
    t = json.loads(test)
    sm = SchemaModelFactory()
    sm.register(t)

    from schemamodels.dynamic import FakeSchema
    fs = FakeSchema(brand_name="yo")

    assert fs.provider_id == 5


def test_numeric_range_support():
    inclusive_range = '''
    {
        "title": "inclusive-range",
        "description": "Blue Blah",
        "type": "object",
        "properties": {
            "rating": {
              "type": "number",
              "minimum": 0,
              "maximum": 5
            }
        }
    }
    '''
    exclusive_max_range = '''
    {
        "title": "exclusive-max-range",
        "description": "Blue Blah",
        "type": "object",
        "properties": {
            "rating": {
              "type": "number",
              "minimum": 0,
              "exclusiveMaximum": 5
            }
        }
    }
    '''
    exclusive_min_range = '''
    {
        "title": "exclusive-min-range",
        "description": "Blue Blah",
        "type": "object",
        "properties": {
            "rating": {
              "type": "number",
              "exclusiveMinimum": 0,
              "maximum": 5
            }
        }
    }
    '''
    irange = json.loads(inclusive_range)
    emaxrange = json.loads(exclusive_max_range)
    eminrange = json.loads(exclusive_min_range)
    sm = SchemaModelFactory()
    sm.register(irange)
    sm.register(eminrange)
    sm.register(emaxrange)

    from schemamodels.dynamic import InclusiveRange, ExclusiveMaxRange, ExclusiveMinRange

    with pytest.raises(Exception):
        fs = InclusiveRange(rating=6)

    with pytest.raises(Exception):
        fs = ExclusiveMaxRange(rating=5)

    with pytest.raises(Exception):
        fs = ExclusiveMinRange(rating=0)
