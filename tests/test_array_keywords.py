# SPDX-FileCopyrightText: 2023-2026 Civic Hacker LLC
# SPDX-License-Identifier: GPL-3.0-or-later

import importlib
import json

import pytest

from schemamodels import exceptions


@pytest.mark.array
@pytest.mark.type
def test_array_type_validation(Factory):
    schemadoc = """
    {
        "title": "array-type-validation",
        "description": "Validation for array type",
        "type": "object",
        "properties": {
            "elements": {
              "type": "array"
            }
        }
    }
    """
    schemadata = json.loads(schemadoc)
    importlib.import_module("schemamodels.dynamic")
    sm = Factory()
    sm.register(schemadata)

    from schemamodels.dynamic import ArrayTypeValidation

    valid1 = ArrayTypeValidation(elements=[1, 2, 3])
    assert valid1.elements == [1, 2, 3]

    valid2 = ArrayTypeValidation(elements=["a", "b"])
    assert valid2.elements == ["a", "b"]

    valid3 = ArrayTypeValidation(elements=[])
    assert valid3.elements == []

    valid4 = ArrayTypeValidation(elements=(1, 2))
    assert valid4.elements == (1, 2)

    with pytest.raises(exceptions.ValueTypeViolation):
        ArrayTypeValidation(elements="not an array")

    with pytest.raises(exceptions.ValueTypeViolation):
        ArrayTypeValidation(elements=123)

    with pytest.raises(exceptions.ValueTypeViolation):
        ArrayTypeValidation(elements={"a": 1})

    with pytest.raises(exceptions.ValueTypeViolation):
        ArrayTypeValidation(elements=True)


@pytest.mark.array
@pytest.mark.minItems
def test_array_min_items_keyword_support(Factory):
    schemadoc = """
    {
        "title": "min-items-array",
        "description": "Validation for minItems array keyword",
        "type": "object",
        "properties": {
            "tags": {
              "type": "array",
              "minItems": 3
            }
        }
    }
    """
    schemadata = json.loads(schemadoc)
    importlib.import_module("schemamodels.dynamic")
    sm = Factory()
    sm.register(schemadata)

    from schemamodels.dynamic import MinItemsArray

    MinItemsArray(tags=["a", "b", "c"])
    MinItemsArray(tags=[1, 2, 3, 4])
    MinItemsArray(tags=["x", "y", "z", "w", "v"])

    with pytest.raises(exceptions.ArrayLengthViolation):
        MinItemsArray(tags=[])

    with pytest.raises(exceptions.ArrayLengthViolation):
        MinItemsArray(tags=["a"])

    with pytest.raises(exceptions.ArrayLengthViolation):
        MinItemsArray(tags=["a", "b"])


@pytest.mark.array
@pytest.mark.maxItems
def test_array_max_items_keyword_support(Factory):
    schemadoc = """
    {
        "title": "max-items-array",
        "description": "Validation for maxItems array keyword",
        "type": "object",
        "properties": {
            "tags": {
              "type": "array",
              "maxItems": 3
            }
        }
    }
    """
    schemadata = json.loads(schemadoc)
    importlib.import_module("schemamodels.dynamic")
    sm = Factory()
    sm.register(schemadata)

    from schemamodels.dynamic import MaxItemsArray

    MaxItemsArray(tags=[])
    MaxItemsArray(tags=["a"])
    MaxItemsArray(tags=["a", "b"])
    MaxItemsArray(tags=["a", "b", "c"])

    with pytest.raises(exceptions.ArrayLengthViolation):
        MaxItemsArray(tags=["a", "b", "c", "d"])

    with pytest.raises(exceptions.ArrayLengthViolation):
        MaxItemsArray(tags=[1, 2, 3, 4, 5])


@pytest.mark.array
@pytest.mark.minItems
@pytest.mark.maxItems
def test_array_min_and_max_items_keyword_support(Factory):
    schemadoc = """
    {
        "title": "min-max-items-array",
        "description": "Validation for minItems and maxItems combined",
        "type": "object",
        "properties": {
            "scores": {
              "type": "array",
              "minItems": 2,
              "maxItems": 4
            }
        }
    }
    """
    schemadata = json.loads(schemadoc)
    importlib.import_module("schemamodels.dynamic")
    sm = Factory()
    sm.register(schemadata)

    from schemamodels.dynamic import MinMaxItemsArray

    MinMaxItemsArray(scores=[10, 20])
    MinMaxItemsArray(scores=[10, 20, 30])
    MinMaxItemsArray(scores=[10, 20, 30, 40])

    with pytest.raises(exceptions.ArrayLengthViolation):
        MinMaxItemsArray(scores=[])

    with pytest.raises(exceptions.ArrayLengthViolation):
        MinMaxItemsArray(scores=[10])

    with pytest.raises(exceptions.ArrayLengthViolation):
        MinMaxItemsArray(scores=[10, 20, 30, 40, 50])


@pytest.mark.array
@pytest.mark.uniqueItems
def test_array_unique_items_true_keyword_support(Factory):
    schemadoc = """
    {
        "title": "unique-items-array",
        "description": "Validation for uniqueItems keyword set to true",
        "type": "object",
        "properties": {
            "values": {
              "type": "array",
              "uniqueItems": true
            }
        }
    }
    """
    schemadata = json.loads(schemadoc)
    importlib.import_module("schemamodels.dynamic")
    sm = Factory()
    sm.register(schemadata)

    from schemamodels.dynamic import UniqueItemsArray

    UniqueItemsArray(values=[])
    UniqueItemsArray(values=[1, 2, 3])
    UniqueItemsArray(values=["a", "b", "c"])
    UniqueItemsArray(values=[{"a": 1}, {"a": 2}])
    UniqueItemsArray(values=[[1, 2], [1, 3]])
    # JSON Schema type distinction: integer 1 vs boolean True, integer 0 vs boolean False
    UniqueItemsArray(values=[1, True])
    UniqueItemsArray(values=[0, False])
    UniqueItemsArray(values=[[1, True], [1, 1]])

    with pytest.raises(exceptions.ArrayUniqueElementViolation):
        UniqueItemsArray(values=[1, 1])

    with pytest.raises(exceptions.ArrayUniqueElementViolation):
        UniqueItemsArray(values=[1, 1.0])

    with pytest.raises(exceptions.ArrayUniqueElementViolation):
        UniqueItemsArray(values=["a", "b", "a"])

    with pytest.raises(exceptions.ArrayUniqueElementViolation):
        UniqueItemsArray(values=[{"a": 1}, {"a": 1}])

    with pytest.raises(exceptions.ArrayUniqueElementViolation):
        UniqueItemsArray(values=[{"a": 1, "b": 2}, {"b": 2, "a": 1}])

    with pytest.raises(exceptions.ArrayUniqueElementViolation):
        UniqueItemsArray(values=[[1, 2], [1, 2]])

    with pytest.raises(exceptions.ArrayUniqueElementViolation):
        UniqueItemsArray(values=[[1, True], [1, True]])


@pytest.mark.array
@pytest.mark.uniqueItems
def test_array_unique_items_false_keyword_support(Factory):
    schemadoc = """
    {
        "title": "non-unique-items-array",
        "description": "Validation for uniqueItems keyword set to false",
        "type": "object",
        "properties": {
            "values": {
              "type": "array",
              "uniqueItems": false
            }
        }
    }
    """
    schemadata = json.loads(schemadoc)
    importlib.import_module("schemamodels.dynamic")
    sm = Factory()
    sm.register(schemadata)

    from schemamodels.dynamic import NonUniqueItemsArray

    inst1 = NonUniqueItemsArray(values=[1, 1, 2, 2])
    assert inst1.values == [1, 1, 2, 2]

    inst2 = NonUniqueItemsArray(values=["a", "a", "b"])
    assert inst2.values == ["a", "a", "b"]

    inst3 = NonUniqueItemsArray(values=[{"a": 1}, {"a": 1}])
    assert inst3.values == [{"a": 1}, {"a": 1}]


@pytest.mark.array
@pytest.mark.contains
def test_array_contains_keyword_support(Factory):
    schemadoc = """
    {
        "title": "contains-array",
        "description": "Validation for contains keyword with default minContains 1",
        "type": "object",
        "properties": {
            "items": {
              "type": "array",
              "contains": {
                "type": "number"
              }
            }
        }
    }
    """
    schemadata = json.loads(schemadoc)
    importlib.import_module("schemamodels.dynamic")
    sm = Factory()
    sm.register(schemadata)

    from schemamodels.dynamic import ContainsArray

    ContainsArray(items=[1])
    ContainsArray(items=["a", 2, "b"])
    ContainsArray(items=[1, 2, 3])
    ContainsArray(items=[3.14, "hello"])

    with pytest.raises(exceptions.ArrayElementViolation):
        ContainsArray(items=[])

    with pytest.raises(exceptions.ArrayElementViolation):
        ContainsArray(items=["a", "b", "c"])

    with pytest.raises(exceptions.ArrayElementViolation):
        ContainsArray(items=[True, False, "hello"])


@pytest.mark.array
@pytest.mark.contains
@pytest.mark.minContains
def test_array_contains_with_min_contains_keyword_support(Factory):
    schemadoc = """
    {
        "title": "min-contains-array",
        "description": "Validation for contains with explicit minContains",
        "type": "object",
        "properties": {
            "items": {
              "type": "array",
              "contains": {
                "type": "integer"
              },
              "minContains": 2
            }
        }
    }
    """
    schemadata = json.loads(schemadoc)
    importlib.import_module("schemamodels.dynamic")
    sm = Factory()
    sm.register(schemadata)

    from schemamodels.dynamic import MinContainsArray

    MinContainsArray(items=[1, 2])
    MinContainsArray(items=["a", 1, "b", 2, "c"])
    MinContainsArray(items=[1, 2, 3])

    with pytest.raises(exceptions.ArrayElementViolation):
        MinContainsArray(items=[])

    with pytest.raises(exceptions.ArrayElementViolation):
        MinContainsArray(items=["a", "b", "c"])

    with pytest.raises(exceptions.ArrayElementViolation):
        MinContainsArray(items=["a", 1, "b"])


@pytest.mark.array
@pytest.mark.contains
@pytest.mark.maxContains
def test_array_contains_with_max_contains_keyword_support(Factory):
    schemadoc = """
    {
        "title": "max-contains-array",
        "description": "Validation for contains with explicit maxContains",
        "type": "object",
        "properties": {
            "items": {
              "type": "array",
              "contains": {
                "type": "string"
              },
              "maxContains": 2
            }
        }
    }
    """
    schemadata = json.loads(schemadoc)
    importlib.import_module("schemamodels.dynamic")
    sm = Factory()
    sm.register(schemadata)

    from schemamodels.dynamic import MaxContainsArray

    # Contains defaults minContains to 1, maxContains to 2
    MaxContainsArray(items=["a"])
    MaxContainsArray(items=["a", 1])
    MaxContainsArray(items=["a", "b", 1, 2])

    with pytest.raises(exceptions.ArrayElementViolation):
        MaxContainsArray(items=[])

    with pytest.raises(exceptions.ArrayElementViolation):
        MaxContainsArray(items=[1, 2, 3])

    with pytest.raises(exceptions.ArrayElementViolation):
        MaxContainsArray(items=["a", "b", "c"])

    with pytest.raises(exceptions.ArrayElementViolation):
        MaxContainsArray(items=["a", "b", "c", "d"])


@pytest.mark.array
@pytest.mark.contains
@pytest.mark.minContains
@pytest.mark.maxContains
def test_array_contains_with_min_and_max_contains_keyword_support(Factory):
    schemadoc = """
    {
        "title": "min-max-contains-array",
        "description": "Validation for contains with both minContains and maxContains",
        "type": "object",
        "properties": {
            "items": {
              "type": "array",
              "contains": {
                "type": "string"
              },
              "minContains": 2,
              "maxContains": 3
            }
        }
    }
    """
    schemadata = json.loads(schemadoc)
    importlib.import_module("schemamodels.dynamic")
    sm = Factory()
    sm.register(schemadata)

    from schemamodels.dynamic import MinMaxContainsArray

    MinMaxContainsArray(items=["a", "b"])
    MinMaxContainsArray(items=["a", "b", 1, 2])
    MinMaxContainsArray(items=["a", "b", "c", 1])

    with pytest.raises(exceptions.ArrayElementViolation):
        MinMaxContainsArray(items=[])

    with pytest.raises(exceptions.ArrayElementViolation):
        MinMaxContainsArray(items=["a", 1, 2])

    with pytest.raises(exceptions.ArrayElementViolation):
        MinMaxContainsArray(items=["a", "b", "c", "d"])


@pytest.mark.array
@pytest.mark.contains
@pytest.mark.minContains
def test_array_min_contains_zero_keyword_support(Factory):
    schemadoc = """
    {
        "title": "zero-min-contains-array",
        "description": "Validation for contains with minContains set to 0",
        "type": "object",
        "properties": {
            "items": {
              "type": "array",
              "contains": {
                "type": "number"
              },
              "minContains": 0
            }
        }
    }
    """
    schemadata = json.loads(schemadoc)
    importlib.import_module("schemamodels.dynamic")
    sm = Factory()
    sm.register(schemadata)

    from schemamodels.dynamic import ZeroMinContainsArray

    ZeroMinContainsArray(items=[])
    ZeroMinContainsArray(items=["a", "b", "c"])
    ZeroMinContainsArray(items=[1, 2])


@pytest.mark.array
@pytest.mark.minContains
@pytest.mark.maxContains
def test_array_min_and_max_contains_without_contains_ignored(Factory):
    schemadoc = """
    {
        "title": "no-contains-array",
        "description": "Validation when minContains and maxContains are present without contains",
        "type": "object",
        "properties": {
            "items": {
              "type": "array",
              "minContains": 5,
              "maxContains": 1
            }
        }
    }
    """
    schemadata = json.loads(schemadoc)
    importlib.import_module("schemamodels.dynamic")
    sm = Factory()
    sm.register(schemadata)

    from schemamodels.dynamic import NoContainsArray

    NoContainsArray(items=[1, 2])
    NoContainsArray(items=[])
    NoContainsArray(items=["a", "b", "c", "d", "e", "f"])


@pytest.mark.array
@pytest.mark.contains
@pytest.mark.minContains
def test_array_contains_boolean_subschema(Factory):
    schemadoc = """
    {
        "title": "bool-contains-array",
        "description": "Validation for boolean subschema in contains",
        "type": "object",
        "properties": {
            "items": {
              "type": "array",
              "contains": true,
              "minContains": 2
            }
        }
    }
    """
    schemadata = json.loads(schemadoc)
    importlib.import_module("schemamodels.dynamic")
    sm = Factory()
    sm.register(schemadata)

    from schemamodels.dynamic import BoolContainsArray

    BoolContainsArray(items=["a", 1])
    BoolContainsArray(items=[1, 2, 3])

    with pytest.raises(exceptions.ArrayElementViolation):
        BoolContainsArray(items=["only_one"])

    with pytest.raises(exceptions.ArrayElementViolation):
        BoolContainsArray(items=[])


@pytest.mark.array
@pytest.mark.contains
def test_array_contains_complex_subschema(Factory):
    schemadoc = """
    {
        "title": "complex-contains-array",
        "description": "Validation for complex subschema in contains",
        "type": "object",
        "properties": {
            "scores": {
              "type": "array",
              "contains": {
                "type": "integer",
                "minimum": 10,
                "maximum": 20
              }
            }
        }
    }
    """
    schemadata = json.loads(schemadoc)
    importlib.import_module("schemamodels.dynamic")
    sm = Factory()
    sm.register(schemadata)

    from schemamodels.dynamic import ComplexContainsArray

    ComplexContainsArray(scores=[5, 15, 25])
    ComplexContainsArray(scores=[10])
    ComplexContainsArray(scores=[20])

    with pytest.raises(exceptions.ArrayElementViolation):
        ComplexContainsArray(scores=[5, 9, 21, 25])

    with pytest.raises(exceptions.ArrayElementViolation):
        ComplexContainsArray(scores=[])

    with pytest.raises(exceptions.ArrayElementViolation):
        ComplexContainsArray(scores=["15"])


@pytest.mark.array
@pytest.mark.minItems
@pytest.mark.maxItems
@pytest.mark.uniqueItems
@pytest.mark.contains
@pytest.mark.minContains
@pytest.mark.maxContains
def test_array_comprehensive_keywords_combination(Factory):
    schemadoc = """
    {
        "title": "comprehensive-array-keywords",
        "description": "Comprehensive combination of array keywords",
        "type": "object",
        "properties": {
            "tags": {
              "type": "array",
              "minItems": 2,
              "maxItems": 5,
              "uniqueItems": true
            },
            "scores": {
              "type": "array",
              "contains": {
                "type": "number"
              },
              "minContains": 1,
              "maxContains": 2
            }
        }
    }
    """
    schemadata = json.loads(schemadoc)
    importlib.import_module("schemamodels.dynamic")
    sm = Factory()
    sm.register(schemadata)

    from schemamodels.dynamic import ComprehensiveArrayKeywords

    valid = ComprehensiveArrayKeywords(
        tags=["python", "pytest"],
        scores=["initial", 95],
    )
    assert valid.tags == ["python", "pytest"]
    assert valid.scores == ["initial", 95]

    # tags minItems violation
    with pytest.raises(exceptions.ArrayLengthViolation):
        ComprehensiveArrayKeywords(tags=["python"], scores=[95])

    # tags maxItems violation
    with pytest.raises(exceptions.ArrayLengthViolation):
        ComprehensiveArrayKeywords(tags=["a", "b", "c", "d", "e", "f"], scores=[95])

    # tags uniqueItems violation
    with pytest.raises(exceptions.ArrayUniqueElementViolation):
        ComprehensiveArrayKeywords(tags=["python", "python"], scores=[95])

    # scores minContains violation (0 number matches)
    with pytest.raises(exceptions.ArrayElementViolation):
        ComprehensiveArrayKeywords(tags=["python", "pytest"], scores=["a", "b"])

    # scores maxContains violation (3 number matches)
    with pytest.raises(exceptions.ArrayElementViolation):
        ComprehensiveArrayKeywords(tags=["python", "pytest"], scores=[10, 20, 30])
