from jsonschema import validators
import json
import importlib
from dataclasses import make_dataclass, FrozenInstanceError

from schemamodels import SchemaModelFactory, exceptions, abstract


import pytest

def test_enforce_required():
    test = '''
    {
        "$id": "https://schema.dev/fake-schema.schema.json",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "required-schema",
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
        from schemamodels.dynamic import RequiredSchema
    except exceptions.RequiredPropertyViolation:
        assert False

    with pytest.raises(TypeError):
        RequiredSchema()
        RequiredSchema(provider_id=1)


def test_immutability():
    test = '''
    {
        "$id": "https://schema.dev/fake-schema.schema.json",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "immutable-schema",
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

    from schemamodels.dynamic import ImmutableSchema
    fs = ImmutableSchema(provider_id=1, brand_name="yo")

    with pytest.raises(FrozenInstanceError):
        fs.provider_id = 3


def test_default_support():
    test = '''
    {
        "$id": "https://schema.dev/fake-schema.schema.json",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "default-schema",
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

    from schemamodels.dynamic import DefaultSchema
    fs = DefaultSchema(brand_name="yo")

    assert fs.provider_id == 5


@pytest.mark.range
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
    sm = SchemaModelFactory(schemas=[eminrange, emaxrange])
    sm.register(irange)

    from schemamodels.dynamic import InclusiveRange, ExclusiveMaxRange, ExclusiveMinRange

    with pytest.raises(exceptions.RangeConstraintViolation):
        fs = InclusiveRange(rating=6)

    with pytest.raises(exceptions.RangeConstraintViolation):
        fs = ExclusiveMaxRange(rating=5)

    with pytest.raises(exceptions.RangeConstraintViolation):
        fs = ExclusiveMinRange(rating=0)


@pytest.mark.type
def test_type_enforcement():
    test = '''
    {
        "$id": "https://schema.dev/fake-schema.schema.json",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "type-schema",
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

    from schemamodels.dynamic import TypeSchema
    with pytest.raises(exceptions.ValueTypeViolation):
        TypeSchema(provider_id="a", brand_name="b")

    with pytest.raises(exceptions.ValueTypeViolation):
        TypeSchema(provider_id=1, brand_name=1)


@pytest.mark.custom
def test_custom_malformed_errorhandler():
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

    class MyCustomErrorHandler(abstract.BaseErrorHandler):
        pass

    t = json.loads(test)

    with pytest.raises(TypeError):
        sm = SchemaModelFactory(error_handler=MyCustomErrorHandler)

    lib = importlib.import_module('schemamodels.dynamic')
    assert not hasattr(lib, 'FakeSchema')


@pytest.mark.custom
def test_custom_malformed_renderer():
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

    class MyCustomRenderer(abstract.BaseRenderer):
        pass

    t = json.loads(test)
    with pytest.raises(TypeError):
        sm = SchemaModelFactory(renderer=MyCustomRenderer)

    lib = importlib.import_module('schemamodels.dynamic')
    assert not hasattr(lib, 'FakeSchema')
