# SPDX-FileCopyrightText: 2023 Civic Hacker, LLC <opensource@civichacker.com>
# SPDX-License-Identifier: GPL-3.0-or-later

from jsonschema import validators
import json
import importlib
from dataclasses import make_dataclass, FrozenInstanceError

from schemamodels import SchemaModelFactory, exceptions, bases, COMPARISONS
from schemamodels import generate_functors


import pytest


def test_absent_is_not_none():
    test = '''
    {
        "$id": "https://schema.dev/fake-schema.schema.json",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "absent-schema",
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
    t = json.loads(test)
    sm = SchemaModelFactory()

    try:
        assert sm.register(t)
        from schemamodels.dynamic import AbsentSchema
    except exceptions.RequiredPropertyViolation:
        assert False

    AbsentSchema(provider_id=1)


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
    with pytest.raises(exceptions.ValueTypeViolation):
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
              "description": "this is a description",
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
              "description": "this is a description",
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
              "description": "this is a description",
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
def test_numeric_multiple_support():
    multipleof = '''
    {
        "title": "multiple-of",
        "description": "Blue Blah",
        "type": "object",
        "properties": {
            "rating": {
              "description": "this is a description",
              "type": "number",
              "multipleOf": 7
            }
        }
    }
    '''
    multi = json.loads(multipleof)
    sm = SchemaModelFactory()
    sm.register(multi)

    from schemamodels.dynamic import MultipleOf

    with pytest.raises(exceptions.RangeConstraintViolation):
        fs = MultipleOf(rating=20)


@pytest.mark.string
def test_string_maxlength_support():
    maxlength = '''
    {
        "title": "max-length",
        "description": "Blue Blah",
        "type": "object",
        "properties": {
            "brand_name": {
              "description": "this is a description",
              "type": "string",
              "minLength": 2,
              "maxLength": 5
            }
        }
    }
    '''
    multi = json.loads(maxlength)
    sm = SchemaModelFactory()
    sm.register(multi)

    from schemamodels.dynamic import MaxLength

    fs = MaxLength(brand_name="abcd")
    with pytest.raises(exceptions.LengthConstraintViolation):
        fs = MaxLength(brand_name="abcdefgh")
    with pytest.raises(exceptions.LengthConstraintViolation):
        fs = MaxLength(brand_name="a")


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
              "description": "this is a description",
              "type": "integer"
            },
            "brand_name": {
              "description": "this is a description",
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
              "description": "this is a description",
              "type": "integer"
            },
            "brand_name": {
              "description": "this is a description",
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
              "description": "this is a description",
              "type": "integer"
            },
            "brand_name": {
              "description": "this is a description",
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
              "description": "this is a description",
              "anyOf": [
                {"type": "integer"},
                {"type": "number"}
              ]
            },
            "brand_name": {
              "description": "this is a description",
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
    AnyOfSchema(provider_id=1.4, brand_name="a")
    AnyOfSchema(provider_id=4, brand_name="a")
    with pytest.raises(exceptions.SubSchemaFailureViolation):
        AnyOfSchema(provider_id="s", brand_name="a")


@pytest.mark.allof
def test_allof_support():
    allof = '''
    {
        "$id": "https://schema.dev/fake-schema.schema.json",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "all-of-schema",
        "description": "Blue Blah",
        "type": "object",
        "properties": {
            "provider_id": {
              "description": "this is a description",
              "type": "integer"
            },
            "brand_name": {
              "description": "this is a description",
              "allOf": [
                {"type": "string"},
                {"maxLength": 5}
              ]
            }
        }
    }
    '''

    t = json.loads(allof)
    sm = SchemaModelFactory()
    sm.register(t)

    lib = importlib.import_module('schemamodels.dynamic')

    assert hasattr(lib, 'AllOfSchema')

    AllOfSchema = getattr(lib, 'AllOfSchema')
    AllOfSchema(provider_id=1343, brand_name="abcd")
    with pytest.raises(exceptions.SubSchemaFailureViolation):
        AllOfSchema(provider_id=1343, brand_name="abcdefgh")


@pytest.mark.oneof
def test_oneof_support():
    oneof = '''
    {
        "$id": "https://schema.dev/fake-schema.schema.json",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "one-of-schema",
        "description": "Blue Blah",
        "type": "object",
        "properties": {
            "provider_id": {
              "description": "this is a description",
                "oneOf": [
                    { "type": "number", "multipleOf": 5 },
                    { "type": "number", "multipleOf": 3 }
                ]
            },
            "brand_name": {
              "description": "this is a description",
                "type": "string"
            }
        }
    }
    '''

    t = json.loads(oneof)
    sm = SchemaModelFactory()
    sm.register(t)

    lib = importlib.import_module('schemamodels.dynamic')

    assert hasattr(lib, 'OneOfSchema')

    OneOfSchema = getattr(lib, 'OneOfSchema')
    OneOfSchema(provider_id=3, brand_name="abcd")
    OneOfSchema(provider_id=5, brand_name="abcd")
    with pytest.raises(exceptions.SubSchemaFailureViolation):
        OneOfSchema(provider_id=15, brand_name="abcde")


@pytest.mark.not_
def test_not_support():
    _not = '''
    {
        "$id": "https://schema.dev/fake-schema.schema.json",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "not-schema",
        "description": "Blue Blah",
        "type": "object",
        "properties": {
            "provider_id": {
              "description": "this is a description",
                "not": {
                    "type": "string"
                }
            },
            "brand_name": {
              "description": "this is a description",
                "type": "string"
            }
        }
    }
    '''

    t = json.loads(_not)
    sm = SchemaModelFactory()
    sm.register(t)

    lib = importlib.import_module('schemamodels.dynamic')

    assert hasattr(lib, 'NotSchema')

    NotSchema = getattr(lib, 'NotSchema')
    NotSchema(provider_id=5, brand_name="abcd")
    with pytest.raises(exceptions.SubSchemaFailureViolation):
        NotSchema(provider_id="welp", brand_name="abcde")


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


@pytest.mark.cell
def test_functor_generator():
    anyof = '''
    {
        "$id": "https://schema.dev/fake-schema.schema.json",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "any-of-schema",
        "description": "Blue Blah",
        "type": "object",
        "properties": {
            "provider_id": {
              "description": "this is a description",
              "anyOf": [
                {"type": "integer"},
                {"type": "number"}
              ]
            },
            "brand_name": {
              "description": "this is a description",
              "type": "string"
            }
        }
    }
    '''

    t = json.loads(anyof)
    fn = None
    anyof_collection = t['properties']['provider_id'].get('anyOf', [])
    funcs = map(lambda s: generate_functors(s), anyof_collection)
    real = lambda value: map(lambda f: f['type'](value), funcs)
    print({'anyOf': real})
    fn = {'anyOf': real}

    f = generate_functors(t['properties']['provider_id'])
    assert next(iter(fn.values()))(1.0)
    assert next(iter(fn.values()))(1)
    assert any(list(next(iter(fn.values()))(1.0)))
    assert all(list(next(iter(fn.values()))("e")))


@pytest.mark.enum
def test_enum_support():
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

    t = json.loads(enum)
    sm = SchemaModelFactory()
    sm.register(t)

    lib = importlib.import_module('schemamodels.dynamic')

    assert hasattr(lib, 'EnumSchema')

    EnumSchema = getattr(lib, 'EnumSchema')
    EnumSchema(handiness="left", brand_name="abcd")
    with pytest.raises(exceptions.ValueTypeViolation):
        EnumSchema(handiness="welp", brand_name="abcde")


@pytest.mark.export
def test_export_funcs():
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

    t = json.loads(enum)
    sm = SchemaModelFactory()
    sm.register(t)

    lib = importlib.import_module('schemamodels.dynamic')

    assert hasattr(lib, 'EnumSchema')

    EnumSchema = getattr(lib, 'EnumSchema')
    e = EnumSchema(handiness="left", brand_name="abcd")
    assert e.tocsv() == "left,abcd"
    assert e.tocsv(header=True) == "handiness,brand_name\nleft,abcd"
    assert e.todict() == {"handiness": "left", "brand_name": "abcd"}
    assert e.tolist() == ["left", "abcd"]
