# SPDX-FileCopyrightText: 2023-2026 Civic Hacker LLC
# SPDX-License-Identifier: GPL-3.0-or-later

import json

import pytest

from schemamodels import exceptions, utils
from schemamodels.bases import ObjectDescriptor


# ============================================================================
# minProperties Keyword Tests
# ============================================================================


@pytest.mark.object
@pytest.mark.minProperties
def test_object_min_properties_keyword_support(Factory):
    schema = {
        "title": "min-props-model",
        "description": "Validation for minProperties object keyword",
        "type": "object",
        "properties": {
            "a": {"type": "integer"},
            "b": {"type": "string"},
            "c": {"type": "boolean"},
        },
        "required": [],
        "minProperties": 2,
    }
    sm = Factory()
    sm.register(schema)

    from schemamodels.dynamic import MinPropsModel

    # Valid: 2 properties provided
    m1 = MinPropsModel(a=1, b="hello")
    assert m1.a == 1
    assert m1.b == "hello"

    # Valid: 3 properties provided
    m2 = MinPropsModel(a=1, b="world", c=True)
    assert m2.a == 1
    assert m2.b == "world"
    assert m2.c is True

    # Invalid: 1 property provided (less than minProperties=2)
    with pytest.raises(exceptions.ObjectPropertiesViolation):
        MinPropsModel(a=1)

    # Invalid: 0 properties provided
    with pytest.raises(exceptions.ObjectPropertiesViolation):
        MinPropsModel()


@pytest.mark.object
@pytest.mark.minProperties
def test_object_min_properties_zero_and_defaults(Factory):
    schema = {
        "title": "min-props-zero-defaults",
        "type": "object",
        "properties": {
            "a": {"type": "integer", "default": 10},
            "b": {"type": "string"},
        },
        "required": [],
        "minProperties": 1,
    }
    sm = Factory()
    sm.register(schema)

    from schemamodels.dynamic import MinPropsZeroDefaults

    # Field 'a' has schema default, so it counts as present
    m1 = MinPropsZeroDefaults()
    assert m1.a == 10

    # minProperties = 0 schema
    schema_zero = {
        "title": "min-props-zero",
        "type": "object",
        "properties": {
            "x": {"type": "string"},
        },
        "required": [],
        "minProperties": 0,
    }
    sm.register(schema_zero)

    from schemamodels.dynamic import MinPropsZero

    m_zero = MinPropsZero()
    assert m_zero.x == ""


@pytest.mark.object
@pytest.mark.minProperties
def test_nested_object_min_properties(Factory):
    schema = {
        "title": "nested-min-props-model",
        "type": "object",
        "properties": {
            "payload": {
                "type": "object",
                "minProperties": 2,
            }
        },
        "required": ["payload"],
    }
    sm = Factory()
    sm.register(schema)

    from schemamodels.dynamic import NestedMinPropsModel

    # Valid payload with 2 properties
    m = NestedMinPropsModel(payload={"k1": "v1", "k2": "v2"})
    assert m.payload == {"k1": "v1", "k2": "v2"}

    # Invalid payload with 1 property
    with pytest.raises(exceptions.ObjectPropertiesViolation):
        NestedMinPropsModel(payload={"k1": "v1"})

    # Invalid payload with 0 properties
    with pytest.raises(exceptions.ObjectPropertiesViolation):
        NestedMinPropsModel(payload={})


# ============================================================================
# maxProperties Keyword Tests
# ============================================================================


@pytest.mark.object
@pytest.mark.maxProperties
def test_object_max_properties_keyword_support(Factory):
    schema = {
        "title": "max-props-model",
        "description": "Validation for maxProperties object keyword",
        "type": "object",
        "properties": {
            "a": {"type": "integer"},
            "b": {"type": "string"},
            "c": {"type": "boolean"},
        },
        "required": [],
        "maxProperties": 2,
    }
    sm = Factory()
    sm.register(schema)

    from schemamodels.dynamic import MaxPropsModel

    # Valid: 0 properties provided
    m0 = MaxPropsModel()
    assert m0.a == 0

    # Valid: 1 property provided
    m1 = MaxPropsModel(a=1)
    assert m1.a == 1

    # Valid: 2 properties provided
    m2 = MaxPropsModel(a=1, b="test")
    assert m2.a == 1
    assert m2.b == "test"

    # Invalid: 3 properties provided (exceeds maxProperties=2)
    with pytest.raises(exceptions.ObjectPropertiesViolation):
        MaxPropsModel(a=1, b="test", c=False)


@pytest.mark.object
@pytest.mark.maxProperties
def test_nested_object_max_properties(Factory):
    schema = {
        "title": "nested-max-props-model",
        "type": "object",
        "properties": {
            "payload": {
                "type": "object",
                "maxProperties": 2,
            }
        },
        "required": ["payload"],
    }
    sm = Factory()
    sm.register(schema)

    from schemamodels.dynamic import NestedMaxPropsModel

    # Valid payload with <= 2 properties
    m = NestedMaxPropsModel(payload={"k1": 1, "k2": 2})
    assert m.payload == {"k1": 1, "k2": 2}

    # Invalid payload with > 2 properties
    with pytest.raises(exceptions.ObjectPropertiesViolation):
        NestedMaxPropsModel(payload={"k1": 1, "k2": 2, "k3": 3})


@pytest.mark.object
@pytest.mark.minProperties
@pytest.mark.maxProperties
def test_object_min_and_max_properties_combined(Factory):
    schema = {
        "title": "min-max-props-model",
        "type": "object",
        "properties": {
            "a": {"type": "integer"},
            "b": {"type": "string"},
            "c": {"type": "boolean"},
            "d": {"type": "number"},
        },
        "required": [],
        "minProperties": 2,
        "maxProperties": 3,
    }
    sm = Factory()
    sm.register(schema)

    from schemamodels.dynamic import MinMaxPropsModel

    # Too few properties (< 2)
    with pytest.raises(exceptions.ObjectPropertiesViolation):
        MinMaxPropsModel(a=1)

    # Valid (2 properties)
    m2 = MinMaxPropsModel(a=1, b="ok")
    assert m2.a == 1
    assert m2.b == "ok"

    # Valid (3 properties)
    m3 = MinMaxPropsModel(a=1, b="ok", c=True)
    assert m3.a == 1
    assert m3.c is True

    # Too many properties (> 3)
    with pytest.raises(exceptions.ObjectPropertiesViolation):
        MinMaxPropsModel(a=1, b="ok", c=True, d=3.14)


# ============================================================================
# dependentRequired Keyword Tests (JSON Schema Spec & Understanding JSON Schema Examples)
# ============================================================================


@pytest.mark.object
@pytest.mark.dependentRequired
def test_dependent_required_customer_account_example(Factory):
    """
    Practical example from https://json-schema.org/understanding-json-schema/reference/conditionals#dependentRequired

    Schema:
    {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "credit_card": { "type": "number" },
        "billing_address": { "type": "string" }
      },
      "required": ["name"],
      "dependentRequired": {
        "credit_card": ["billing_address"]
      }
    }
    """
    schemadoc = """
    {
        "title": "customer-account",
        "type": "object",
        "properties": {
            "name": { "type": "string" },
            "credit_card": { "type": "number" },
            "billing_address": { "type": "string" }
        },
        "required": ["name"],
        "dependentRequired": {
            "credit_card": ["billing_address"]
        }
    }
    """
    schema = json.loads(schemadoc)
    sm = Factory()
    sm.register(schema)

    from schemamodels.dynamic import CustomerAccount

    # 1. Providing a name, credit card, and billing address is valid
    acc1 = CustomerAccount(
        name="John Doe",
        credit_card=5555555555555555,
        billing_address="555 Debtor's Lane",
    )
    assert acc1.name == "John Doe"
    assert acc1.credit_card == 5555555555555555
    assert acc1.billing_address == "555 Debtor's Lane"

    # 2. Providing a billing address without a credit card is valid
    acc2 = CustomerAccount(
        name="John Doe",
        billing_address="555 Debtor's Lane",
    )
    assert acc2.name == "John Doe"
    assert acc2.billing_address == "555 Debtor's Lane"

    # 3. Providing neither credit card nor billing address is valid
    acc3 = CustomerAccount(name="John Doe")
    assert acc3.name == "John Doe"

    # 4. Providing a credit card without a billing address is invalid
    with pytest.raises(exceptions.RequiredPropertyViolation):
        CustomerAccount(name="John Doe", credit_card=5555555555555555)


@pytest.mark.object
@pytest.mark.dependentRequired
def test_dependent_required_multiple_dependencies(Factory):
    schema = {
        "title": "multi-dep-account",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "credit_card": {"type": "number"},
            "billing_address": {"type": "string"},
            "security_code": {"type": "string"},
        },
        "required": ["name"],
        "dependentRequired": {
            "credit_card": ["billing_address", "security_code"],
        },
    }
    sm = Factory()
    sm.register(schema)

    from schemamodels.dynamic import MultiDepAccount

    # Valid: credit card with both required dependent fields
    acc = MultiDepAccount(
        name="Alice",
        credit_card=12345678,
        billing_address="123 Main St",
        security_code="999",
    )
    assert acc.security_code == "999"

    # Invalid: credit card missing security_code
    with pytest.raises(exceptions.RequiredPropertyViolation):
        MultiDepAccount(
            name="Alice",
            credit_card=12345678,
            billing_address="123 Main St",
        )

    # Invalid: credit card missing both billing_address and security_code (ExceptionGroup with 2 errors)
    with pytest.raises(ExceptionGroup) as exc_info:
        MultiDepAccount(
            name="Alice",
            credit_card=12345678,
        )
    assert len(exc_info.value.exceptions) == 2
    for err in exc_info.value.exceptions:
        assert isinstance(err, exceptions.RequiredPropertyViolation)


@pytest.mark.object
@pytest.mark.dependentRequired
def test_dependent_required_bidirectional_dependencies(Factory):
    schema = {
        "title": "bidirectional-deps",
        "type": "object",
        "properties": {
            "credit_card": {"type": "number"},
            "billing_address": {"type": "string"},
        },
        "required": [],
        "dependentRequired": {
            "credit_card": ["billing_address"],
            "billing_address": ["credit_card"],
        },
    }
    sm = Factory()
    sm.register(schema)

    from schemamodels.dynamic import BidirectionalDeps

    # Valid: neither present
    m0 = BidirectionalDeps()
    assert m0.credit_card == 0.0

    # Valid: both present
    m_both = BidirectionalDeps(credit_card=1234, billing_address="Road 1")
    assert m_both.credit_card == 1234
    assert m_both.billing_address == "Road 1"

    # Invalid: credit_card without billing_address
    with pytest.raises(exceptions.RequiredPropertyViolation):
        BidirectionalDeps(credit_card=1234)

    # Invalid: billing_address without credit_card
    with pytest.raises(exceptions.RequiredPropertyViolation):
        BidirectionalDeps(billing_address="Road 1")


@pytest.mark.object
@pytest.mark.dependentRequired
def test_nested_object_dependent_required(Factory):
    schema = {
        "title": "nested-dep-req-model",
        "type": "object",
        "properties": {
            "options": {
                "type": "object",
                "dependentRequired": {
                    "ssl": ["cert", "key"],
                },
            }
        },
        "required": ["options"],
    }
    sm = Factory()
    sm.register(schema)

    from schemamodels.dynamic import NestedDepReqModel

    # Valid: ssl present with cert and key
    m1 = NestedDepReqModel(options={"ssl": True, "cert": "cert.pem", "key": "key.pem"})
    assert m1.options["cert"] == "cert.pem"

    # Valid: ssl not present
    m2 = NestedDepReqModel(options={"port": 8080})
    assert m2.options["port"] == 8080

    # Invalid: ssl present without cert and key
    with pytest.raises(exceptions.RequiredPropertyViolation):
        NestedDepReqModel(options={"ssl": True})


# ============================================================================
# Schema-Level Registration Validation (Malformed Schema Violation Tests)
# ============================================================================


@pytest.mark.object
@pytest.mark.struct
def test_object_keywords_schema_validation(Factory):
    sm = Factory()

    # Valid schema with all object keywords
    valid_schema = {
        "title": "valid-object-schema",
        "type": "object",
        "properties": {
            "a": {"type": "string"},
            "b": {"type": "integer"},
        },
        "required": ["a"],
        "minProperties": 1,
        "maxProperties": 2,
        "dependentRequired": {"b": ["a"]},
    }
    assert sm.register(valid_schema)

    # Malformed minProperties: negative integer
    with pytest.raises(exceptions.MalformedSchemaViolation):
        sm.register(
            {
                "title": "bad-min-props-1",
                "type": "object",
                "properties": {"a": {"type": "string"}},
                "minProperties": -1,
            }
        )

    # Malformed minProperties: string
    with pytest.raises(exceptions.MalformedSchemaViolation):
        sm.register(
            {
                "title": "bad-min-props-2",
                "type": "object",
                "properties": {"a": {"type": "string"}},
                "minProperties": "2",
            }
        )

    # Malformed minProperties: boolean (True is int in Python, must not be accepted)
    with pytest.raises(exceptions.MalformedSchemaViolation):
        sm.register(
            {
                "title": "bad-min-props-3",
                "type": "object",
                "properties": {"a": {"type": "string"}},
                "minProperties": True,
            }
        )

    # Malformed maxProperties: negative integer
    with pytest.raises(exceptions.MalformedSchemaViolation):
        sm.register(
            {
                "title": "bad-max-props-1",
                "type": "object",
                "properties": {"a": {"type": "string"}},
                "maxProperties": -5,
            }
        )

    # Malformed maxProperties: float
    with pytest.raises(exceptions.MalformedSchemaViolation):
        sm.register(
            {
                "title": "bad-max-props-2",
                "type": "object",
                "properties": {"a": {"type": "string"}},
                "maxProperties": 2.5,
            }
        )

    # Malformed dependentRequired: not an object (array)
    with pytest.raises(exceptions.MalformedSchemaViolation):
        sm.register(
            {
                "title": "bad-dep-req-1",
                "type": "object",
                "properties": {"a": {"type": "string"}},
                "dependentRequired": ["a"],
            }
        )

    # Malformed dependentRequired: property value is not an array
    with pytest.raises(exceptions.MalformedSchemaViolation):
        sm.register(
            {
                "title": "bad-dep-req-2",
                "type": "object",
                "properties": {"a": {"type": "string"}, "b": {"type": "string"}},
                "dependentRequired": {"a": "b"},
            }
        )

    # Malformed dependentRequired: array elements are not strings
    with pytest.raises(exceptions.MalformedSchemaViolation):
        sm.register(
            {
                "title": "bad-dep-req-3",
                "type": "object",
                "properties": {"a": {"type": "string"}, "b": {"type": "string"}},
                "dependentRequired": {"a": [123]},
            }
        )

    # Malformed dependentRequired: array has duplicate strings
    with pytest.raises(exceptions.MalformedSchemaViolation):
        sm.register(
            {
                "title": "bad-dep-req-4",
                "type": "object",
                "properties": {"a": {"type": "string"}, "b": {"type": "string"}},
                "dependentRequired": {"a": ["b", "b"]},
            }
        )


# ============================================================================
# Subschema Validation Tests
# ============================================================================


@pytest.mark.object
@pytest.mark.subschema
def test_validate_subschema_object_keywords():
    subschema_min = {"type": "object", "minProperties": 2}
    assert utils.validate_subschema(subschema_min, {"a": 1, "b": 2}) is True
    assert utils.validate_subschema(subschema_min, {"a": 1}) is False

    subschema_max = {"type": "object", "maxProperties": 2}
    assert utils.validate_subschema(subschema_max, {"a": 1}) is True
    assert utils.validate_subschema(subschema_max, {"a": 1, "b": 2, "c": 3}) is False

    subschema_dep = {"type": "object", "dependentRequired": {"card": ["addr"]}}
    assert utils.validate_subschema(subschema_dep, {"card": 123, "addr": "NYC"}) is True
    assert utils.validate_subschema(subschema_dep, {"name": "John"}) is True
    assert utils.validate_subschema(subschema_dep, {"card": 123}) is False


# ============================================================================
# Standalone ObjectDescriptor Tests
# ============================================================================


@pytest.mark.v2
@pytest.mark.descriptor
def test_standalone_object_descriptor_validation():
    class DummyTarget:
        pass

    target = DummyTarget()

    # minProperties descriptor
    desc_min = ObjectDescriptor(metadata={"minProperties": 2})
    desc_min.__set_name__(DummyTarget, "obj_field")

    desc_min.__set__(target, {"a": 1, "b": 2})
    assert target.obj_field == {"a": 1, "b": 2}

    with pytest.raises(exceptions.ObjectPropertiesViolation):
        desc_min.__set__(target, {"a": 1})

    # maxProperties descriptor
    desc_max = ObjectDescriptor(metadata={"maxProperties": 1})
    desc_max.__set_name__(DummyTarget, "obj_field2")

    desc_max.__set__(target, {"a": 1})
    assert target.obj_field2 == {"a": 1}

    with pytest.raises(exceptions.ObjectPropertiesViolation):
        desc_max.__set__(target, {"a": 1, "b": 2})

    # dependentRequired descriptor
    desc_dep = ObjectDescriptor(metadata={"dependentRequired": {"a": ["b"]}})
    desc_dep.__set_name__(DummyTarget, "obj_field3")

    desc_dep.__set__(target, {"a": 1, "b": 2})
    assert target.obj_field3 == {"a": 1, "b": 2}

    desc_dep.__set__(target, {"c": 3})
    assert target.obj_field3 == {"c": 3}

    with pytest.raises(exceptions.RequiredPropertyViolation):
        desc_dep.__set__(target, {"a": 1})
