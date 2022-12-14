from jsonschema import validators
import json
import importlib
from dataclasses import make_dataclass, FrozenInstanceError

from schemamodels import SchemaModelFactory, exceptions, bases, COMPARISONS


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

    with pytest.raises(exceptions.ValueTypeViolation):
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


@pytest.mark.multi
def test_numeric_multiples_support():
    multiplesof = '''
    {
        "title": "multiples-of",
        "description": "Blue Blah",
        "type": "object",
        "properties": {
            "rating": {
              "type": "number",
              "multiplesOf": 7
            }
        }
    }
    '''
    multi = json.loads(multiplesof)
    sm = SchemaModelFactory()
    sm.register(multi)

    from schemamodels.dynamic import MultiplesOf

    with pytest.raises(exceptions.RangeConstraintViolation):
        fs = MultiplesOf(rating=20)



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

    class MyCustomErrorHandler(bases.BaseErrorHandler):
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

    class MyCustomRenderer(bases.BaseRenderer):
        pass

    t = json.loads(test)
    with pytest.raises(TypeError):
        sm = SchemaModelFactory(renderer=MyCustomRenderer)

    lib = importlib.import_module('schemamodels.dynamic')
    assert not hasattr(lib, 'FakeSchema')


@pytest.mark.anyof
def test_anyof_support():
    anyof = '''
    {
        "$id": "https://schema.dev/fake-schema.schema.json",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "any-of-schema",
        "description": "Blue Blah",
        "type": "object",
        "properties": {
            "provider_id": {
              "anyOf": [
                {"type": "integer"},
                {"type": "number"}
              ]
            },
            "brand_name": {
              "type": "string"
            }
        }
    }
    '''

    t = json.loads(anyof)
    sm = SchemaModelFactory()
    sm.register(t)

    lib = importlib.import_module('schemamodels.dynamic')

    assert hasattr(lib, 'AnyOfSchema')

    AnyOfSchema = getattr(lib, 'AnyOfSchema')
    AnyOfSchema(provider_id=1.0, brand_name="a")
    AnyOfSchema(provider_id=1, brand_name="a")
    with pytest.raises(exceptions.ValueTypeViolation):
        AnyOfSchema(provider_id="s", brand_name="a")

@pytest.mark.cell
def test_type_comparison():
    schema = {'type': 'number', 'maximum': 5, 'value': 10}
    assert COMPARISONS['type'](schema['type'])(schema['value'])


@pytest.mark.cell
def test_range_comparison():
    over = {'type': 'number', 'maximum': 5, 'value': 10}
    under = {'type': 'number', 'maximum': 5, 'value': 3}
    assert not COMPARISONS['maximum'](over['maximum'])(over['value'])
    assert COMPARISONS['maximum'](under['maximum'])(under['value'])


@pytest.mark.cell
def test_range_minmax_comparison():
    over = {'type': 'number', 'minimum': 0, 'maximum': 5, 'value': 10}
    under = {'type': 'number', 'minimum': 0, 'maximum': 5, 'value': -3}
    assert not COMPARISONS['maximum'](over['maximum'])(over['value'])
    assert COMPARISONS['minimum'](over['minimum'])(over['value'])
    assert not COMPARISONS['minimum'](under['minimum'])(under['value'])
    assert COMPARISONS['maximum'](under['maximum'])(under['value'])
