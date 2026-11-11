# SPDX-FileCopyrightText: 2023-2026 Civic Hacker LLC
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import make_dataclass
from typing import TypeVar

import pytest

from schemamodels import SchemaModelFactoryV2, bases, v2
from schemamodels import exceptions as e
from schemamodels.constants import REQUIRED_MISSING

T = TypeVar("T", str, int, float, bool, None)
C = TypeVar("C", list, tuple)
A = TypeVar("A")


@pytest.mark.v2
def test_new_iterable(simple_schema):
    obj_gen = v2.process_keys(simple_schema)
    for k in obj_gen:
        assert k in simple_schema.get("properties")


@pytest.mark.v2
def test_scalar_descriptor(simple_schema):
    SimpleSchema = make_dataclass(
        "SimpleSchema",
        [
            (
                "name",
                bases.StringDescriptor,
                bases.StringDescriptor(metadata={"maxLength": 3}),
            ),
            ("id", bases.NumberDescriptor, bases.NumberDescriptor()),
        ],
    )

    ss = SimpleSchema(name="nic", id=2)
    assert ss.name == "nic"
    assert ss.id == 2

    with pytest.raises(e.LengthConstraintViolation):
        SimpleSchema(name="nice", id="nice")


@pytest.mark.anyof
@pytest.mark.v2
def test_anyof_descriptor(anyof_schema):
    passed_in_types = [int, float]

    AnyOfDescriptor = SchemaModelFactoryV2.dynamic_descriptor(passed_in_types)

    AnyOfSchema = make_dataclass(
        "AnyOfSchema",
        [
            (
                "brand_name",
                bases.StringDescriptor,
                bases.StringDescriptor(metadata={"maxLength": 3}),
            ),
            ("provider_id", AnyOfDescriptor, AnyOfDescriptor()),
        ],
    )

    ss = AnyOfSchema(brand_name="nic", provider_id=2)
    assert ss.provider_id == 2

    with pytest.raises(e.LengthConstraintViolation):
        AnyOfSchema(brand_name="nice", provider_id=2)

    with pytest.raises(e.ValueTypeViolation):
        AnyOfSchema(brand_name="nic", provider_id="an-id")


@pytest.mark.v2
@pytest.mark.descriptor
@pytest.mark.anyof
def test_dynamic_descriptor(anyof_schema):
    # Arrange
    passed_in_types = [int, str]  # Drives the type check

    AnyOfDescriptor = SchemaModelFactoryV2.dynamic_descriptor(passed_in_types)
    # Act
    AnyOfSchema = make_dataclass(
        "AnyOfSchema",
        [
            ("provider_id", AnyOfDescriptor, AnyOfDescriptor()),
        ]
        + [
            (
                "brand_name",
                bases.StringDescriptor,
                bases.StringDescriptor(metadata={"maxLength": 3}),
            ),
        ],
    )

    # Test
    assert AnyOfSchema(brand_name="nic", provider_id=2)
    assert AnyOfSchema(brand_name="nic", provider_id="str")

    with pytest.raises(e.LengthConstraintViolation):
        AnyOfSchema(brand_name="nice", provider_id=2)

    with pytest.raises(e.ValueTypeViolation):
        AnyOfSchema(brand_name="nic", provider_id=3.2)


@pytest.mark.v2
@pytest.mark.descriptor
def test_string_descriptor():
    StringSchema = make_dataclass(
        "StringSchema",
        [
            (
                "val",
                bases.StringDescriptor,
                bases.StringDescriptor(
                    default="hello", metadata={"minLength": 2, "maxLength": 5}
                ),
            )
        ],
    )

    s1 = StringSchema(val="world")
    assert s1.val == "world"

    s_default = StringSchema()
    assert s_default.val == "hello"

    # Type violation
    with pytest.raises(e.ValueTypeViolation):
        StringSchema(val=123)

    # Length violation (too short)
    with pytest.raises(e.LengthConstraintViolation):
        StringSchema(val="a")

    # Length violation (too long)
    with pytest.raises(e.LengthConstraintViolation):
        StringSchema(val="toolongstring")

    EnumStringSchema = make_dataclass(
        "EnumStringSchema",
        [
            (
                "val",
                bases.StringDescriptor,
                bases.StringDescriptor(metadata={"enum": ["apple", "banana"]}),
            )
        ],
    )
    e1 = EnumStringSchema(val="apple")
    assert e1.val == "apple"
    with pytest.raises(e.ValueTypeViolation):
        EnumStringSchema(val="orange")


@pytest.mark.v2
@pytest.mark.descriptor
def test_number_descriptor():
    NumberSchema = make_dataclass(
        "NumberSchema",
        [
            (
                "score",
                bases.NumberDescriptor,
                bases.NumberDescriptor(
                    default=10.0,
                    metadata={"minimum": 0.0, "maximum": 100.0, "multipleOf": 0.5},
                ),
            )
        ],
    )

    n1 = NumberSchema(score=50.5)
    assert n1.score == 50.5

    n2 = NumberSchema(score=0)
    assert n2.score == 0

    # Type violation (reject boolean and string)
    with pytest.raises(e.ValueTypeViolation):
        NumberSchema(score=True)

    with pytest.raises(e.ValueTypeViolation):
        NumberSchema(score="50")

    # Range violations
    with pytest.raises(e.RangeConstraintViolation):
        NumberSchema(score=-1.0)

    with pytest.raises(e.RangeConstraintViolation):
        NumberSchema(score=105.0)

    with pytest.raises(e.RangeConstraintViolation):
        NumberSchema(score=50.3)


@pytest.mark.v2
@pytest.mark.descriptor
def test_integer_descriptor():
    IntSchema = make_dataclass(
        "IntSchema",
        [
            (
                "count",
                bases.IntegerDescriptor,
                bases.IntegerDescriptor(
                    default=1,
                    metadata={
                        "exclusiveMinimum": 0,
                        "exclusiveMaximum": 10,
                        "multipleOf": 2,
                    },
                ),
            )
        ],
    )

    i1 = IntSchema(count=4)
    assert i1.count == 4

    # Float rejection
    with pytest.raises(e.ValueTypeViolation):
        IntSchema(count=4.0)

    # Bool rejection
    with pytest.raises(e.ValueTypeViolation):
        IntSchema(count=True)

    # Exclusive bound violations
    with pytest.raises(e.RangeConstraintViolation):
        IntSchema(count=0)

    with pytest.raises(e.RangeConstraintViolation):
        IntSchema(count=10)

    # multipleOf violation
    with pytest.raises(e.RangeConstraintViolation):
        IntSchema(count=3)


@pytest.mark.v2
@pytest.mark.descriptor
def test_boolean_descriptor():
    BoolSchema = make_dataclass(
        "BoolSchema",
        [
            (
                "active",
                bases.BooleanDescriptor,
                bases.BooleanDescriptor(default=True, metadata={"enum": [True, False]}),
            )
        ],
    )

    b1 = BoolSchema(active=False)
    assert b1.active is False

    b_default = BoolSchema()
    assert b_default.active is True

    # Rejection of int or str
    with pytest.raises(e.ValueTypeViolation):
        BoolSchema(active=1)

    with pytest.raises(e.ValueTypeViolation):
        BoolSchema(active="true")


@pytest.mark.v2
@pytest.mark.descriptor
def test_array_descriptor():
    ArraySchema = make_dataclass(
        "ArraySchema",
        [
            (
                "tags",
                bases.ArrayDescriptor,
                bases.ArrayDescriptor(metadata={"allOf": [{"type": "array"}]}),
            )
        ],
    )

    a1 = ArraySchema(tags=["python", "pytest"])
    assert a1.tags == ["python", "pytest"]

    # Non-array rejection
    with pytest.raises(e.ValueTypeViolation):
        ArraySchema(tags="python,pytest")

    with pytest.raises(e.ValueTypeViolation):
        ArraySchema(tags=123)


@pytest.mark.v2
@pytest.mark.descriptor
def test_array_descriptor_min_items():
    MinItemsSchema = make_dataclass(
        "MinItemsSchema",
        [
            (
                "items",
                bases.ArrayDescriptor,
                bases.ArrayDescriptor(metadata={"minItems": 2}),
            )
        ],
    )

    s1 = MinItemsSchema(items=[1, 2])
    assert s1.items == [1, 2]
    s2 = MinItemsSchema(items=["a", "b", "c"])
    assert s2.items == ["a", "b", "c"]
    s3 = MinItemsSchema(items=(1, 2, 3))
    assert s3.items == (1, 2, 3)

    with pytest.raises(e.ArrayLengthViolation):
        MinItemsSchema(items=[])

    with pytest.raises(e.ArrayLengthViolation):
        MinItemsSchema(items=[1])

    with pytest.raises(e.ArrayLengthViolation):
        MinItemsSchema(items=("only_one",))

    # minItems = 0
    ZeroMinSchema = make_dataclass(
        "ZeroMinSchema",
        [
            (
                "items",
                bases.ArrayDescriptor,
                bases.ArrayDescriptor(metadata={"minItems": 0}),
            )
        ],
    )
    assert ZeroMinSchema(items=[]).items == []


@pytest.mark.v2
@pytest.mark.descriptor
def test_array_descriptor_max_items():
    MaxItemsSchema = make_dataclass(
        "MaxItemsSchema",
        [
            (
                "items",
                bases.ArrayDescriptor,
                bases.ArrayDescriptor(metadata={"maxItems": 3}),
            )
        ],
    )

    assert MaxItemsSchema(items=[]).items == []
    assert MaxItemsSchema(items=[1]).items == [1]
    assert MaxItemsSchema(items=[1, 2, 3]).items == [1, 2, 3]
    assert MaxItemsSchema(items=(1, 2)).items == (1, 2)

    with pytest.raises(e.ArrayLengthViolation):
        MaxItemsSchema(items=[1, 2, 3, 4])

    with pytest.raises(e.ArrayLengthViolation):
        MaxItemsSchema(items=(1, 2, 3, 4, 5))


@pytest.mark.v2
@pytest.mark.descriptor
def test_array_descriptor_min_and_max_items():
    BoundedArraySchema = make_dataclass(
        "BoundedArraySchema",
        [
            (
                "items",
                bases.ArrayDescriptor,
                bases.ArrayDescriptor(metadata={"minItems": 2, "maxItems": 4}),
            )
        ],
    )

    assert BoundedArraySchema(items=[1, 2]).items == [1, 2]
    assert BoundedArraySchema(items=[1, 2, 3]).items == [1, 2, 3]
    assert BoundedArraySchema(items=[1, 2, 3, 4]).items == [1, 2, 3, 4]

    with pytest.raises(e.ArrayLengthViolation):
        BoundedArraySchema(items=[1])

    with pytest.raises(e.ArrayLengthViolation):
        BoundedArraySchema(items=[1, 2, 3, 4, 5])


@pytest.mark.v2
@pytest.mark.descriptor
def test_array_descriptor_unique_items():
    UniqueSchema = make_dataclass(
        "UniqueSchema",
        [
            (
                "items",
                bases.ArrayDescriptor,
                bases.ArrayDescriptor(metadata={"uniqueItems": True}),
            )
        ],
    )

    assert UniqueSchema(items=[]).items == []
    assert UniqueSchema(items=[1]).items == [1]
    assert UniqueSchema(items=[1, 2, 3]).items == [1, 2, 3]
    assert UniqueSchema(items=["a", "b", "c"]).items == ["a", "b", "c"]
    assert UniqueSchema(items=[{"a": 1}, {"a": 2}]).items == [{"a": 1}, {"a": 2}]
    assert UniqueSchema(items=[[1, 2], [1, 3]]).items == [[1, 2], [1, 3]]
    # JSON Schema type distinction: integer 1 vs boolean True, integer 0 vs boolean False
    assert UniqueSchema(items=[1, True]).items == [1, True]
    assert UniqueSchema(items=[0, False]).items == [0, False]
    assert UniqueSchema(items=[[1, True], [1, 1]]).items == [[1, True], [1, 1]]

    with pytest.raises(e.ArrayUniqueElementViolation):
        UniqueSchema(items=[1, 1])

    with pytest.raises(e.ArrayUniqueElementViolation):
        UniqueSchema(items=[1, 1.0])

    with pytest.raises(e.ArrayUniqueElementViolation):
        UniqueSchema(items=[1, 2, 3, 1])

    with pytest.raises(e.ArrayUniqueElementViolation):
        UniqueSchema(items=["foo", "bar", "foo"])

    with pytest.raises(e.ArrayUniqueElementViolation):
        UniqueSchema(items=[{"a": 1}, {"a": 1}])

    with pytest.raises(e.ArrayUniqueElementViolation):
        UniqueSchema(items=[{"a": 1, "b": 2}, {"b": 2, "a": 1}])

    with pytest.raises(e.ArrayUniqueElementViolation):
        UniqueSchema(items=[[1, 2], [1, 2]])

    with pytest.raises(e.ArrayUniqueElementViolation):
        UniqueSchema(items=[[1, True], [1, True]])

    # uniqueItems = False allows duplicates
    NonUniqueSchema = make_dataclass(
        "NonUniqueSchema",
        [
            (
                "items",
                bases.ArrayDescriptor,
                bases.ArrayDescriptor(metadata={"uniqueItems": False}),
            )
        ],
    )
    assert NonUniqueSchema(items=[1, 1, 1]).items == [1, 1, 1]


@pytest.mark.v2
@pytest.mark.descriptor
def test_array_descriptor_min_max_contains():
    # minContains and maxContains with contains schema
    ContainsSchema = make_dataclass(
        "ContainsSchema",
        [
            (
                "items",
                bases.ArrayDescriptor,
                bases.ArrayDescriptor(
                    metadata={
                        "contains": {"type": "number"},
                        "minContains": 2,
                        "maxContains": 3,
                    }
                ),
            )
        ],
    )

    # Valid: 2 or 3 numbers
    assert ContainsSchema(items=["a", 1, 2]).items == ["a", 1, 2]
    assert ContainsSchema(items=[1, 2, 3]).items == [1, 2, 3]
    assert ContainsSchema(items=["x", "y", 10, 20]).items == ["x", "y", 10, 20]

    # Less than minContains (2)
    with pytest.raises(e.ArrayElementViolation):
        ContainsSchema(items=["a", "b", "c"])

    with pytest.raises(e.ArrayElementViolation):
        ContainsSchema(items=["a", 1, "b"])

    # More than maxContains (3)
    with pytest.raises(e.ArrayElementViolation):
        ContainsSchema(items=[1, 2, 3, 4])

    with pytest.raises(e.ArrayElementViolation):
        ContainsSchema(items=[1, 2, 3, 4, "a"])

    # contains without minContains defaults to minContains=1
    DefaultContainsSchema = make_dataclass(
        "DefaultContainsSchema",
        [
            (
                "items",
                bases.ArrayDescriptor,
                bases.ArrayDescriptor(metadata={"contains": {"type": "string"}}),
            )
        ],
    )
    assert DefaultContainsSchema(items=[1, 2, "hello"]).items == [1, 2, "hello"]
    with pytest.raises(e.ArrayElementViolation):
        DefaultContainsSchema(items=[1, 2, 3])

    # only maxContains specified
    MaxContainsSchema = make_dataclass(
        "MaxContainsSchema",
        [
            (
                "items",
                bases.ArrayDescriptor,
                bases.ArrayDescriptor(
                    metadata={
                        "contains": {"type": "string"},
                        "maxContains": 1,
                        "minContains": 0,
                    }
                ),
            )
        ],
    )
    assert MaxContainsSchema(items=[1, 2, 3]).items == [1, 2, 3]
    assert MaxContainsSchema(items=[1, "a", 2]).items == [1, "a", 2]
    with pytest.raises(e.ArrayElementViolation):
        MaxContainsSchema(items=["a", "b", 1])

    # minContains: 0 with contains allows 0 matches and empty array
    ZeroMinContainsSchema = make_dataclass(
        "ZeroMinContainsSchema",
        [
            (
                "items",
                bases.ArrayDescriptor,
                bases.ArrayDescriptor(
                    metadata={
                        "contains": {"type": "number"},
                        "minContains": 0,
                    }
                ),
            )
        ],
    )
    assert ZeroMinContainsSchema(items=[]).items == []
    assert ZeroMinContainsSchema(items=["a", "b", "c"]).items == ["a", "b", "c"]
    assert ZeroMinContainsSchema(items=[1, 2]).items == [1, 2]

    # minContains or maxContains without contains has no effect
    NoContainsSchema = make_dataclass(
        "NoContainsSchema",
        [
            (
                "items",
                bases.ArrayDescriptor,
                bases.ArrayDescriptor(
                    metadata={
                        "minContains": 5,
                        "maxContains": 1,
                    }
                ),
            )
        ],
    )
    assert NoContainsSchema(items=[1, 2]).items == [1, 2]
    assert NoContainsSchema(items=[]).items == []

    # boolean subschemas for contains
    BoolContainsSchema = make_dataclass(
        "BoolContainsSchema",
        [
            (
                "items",
                bases.ArrayDescriptor,
                bases.ArrayDescriptor(
                    metadata={
                        "contains": True,
                        "minContains": 2,
                    }
                ),
            )
        ],
    )
    assert BoolContainsSchema(items=["a", 1]).items == ["a", 1]
    with pytest.raises(e.ArrayElementViolation):
        BoolContainsSchema(items=["only_one"])


@pytest.mark.v2
@pytest.mark.descriptor
def test_array_descriptor_comparisons_direct():
    # Test each comparator directly from ArrayDescriptor.COMPARISONS
    min_items_cmp = bases.ArrayDescriptor.COMPARISONS["minItems"]["comparator"](2)
    assert min_items_cmp([1, 2]) is True
    assert min_items_cmp([1, 2, 3]) is True
    assert min_items_cmp([1]) is False
    assert min_items_cmp([]) is False

    max_items_cmp = bases.ArrayDescriptor.COMPARISONS["maxItems"]["comparator"](2)
    assert max_items_cmp([]) is True
    assert max_items_cmp([1, 2]) is True
    assert max_items_cmp([1, 2, 3]) is False

    unique_items_cmp = bases.ArrayDescriptor.COMPARISONS["uniqueItems"]["comparator"](
        True
    )
    assert unique_items_cmp([1, 2, 3]) is True
    assert unique_items_cmp([]) is True
    assert unique_items_cmp([1, 1]) is False
    assert unique_items_cmp([{"a": 1}, {"a": 1}]) is False
    assert unique_items_cmp([{"a": 1}, {"a": 2}]) is True

    non_unique_cmp = bases.ArrayDescriptor.COMPARISONS["uniqueItems"]["comparator"](
        False
    )
    assert non_unique_cmp([1, 1]) is True

    min_contains_cmp = bases.ArrayDescriptor.COMPARISONS["minContains"]["comparator"](2)
    assert min_contains_cmp([1, 2, 3], contains={"type": "number"}) is True
    assert min_contains_cmp(["a", 1], contains={"type": "number"}) is False

    max_contains_cmp = bases.ArrayDescriptor.COMPARISONS["maxContains"]["comparator"](2)
    assert max_contains_cmp([1, 2], contains={"type": "number"}) is True
    assert max_contains_cmp([1, 2, 3], contains={"type": "number"}) is False


@pytest.mark.v2
@pytest.mark.descriptor
def test_schema_model_factory_v2_array_keywords():
    schema = {
        "title": "array-keywords-schema",
        "type": "object",
        "properties": {
            "tags": {
                "type": "array",
                "minItems": 2,
                "maxItems": 4,
                "uniqueItems": True,
            },
            "scores": {
                "type": "array",
                "contains": {"type": "number"},
                "minContains": 1,
                "maxContains": 2,
            },
        },
    }

    SchemaModelFactoryV2(schemas=[schema])
    from schemamodels.dynamic import ArrayKeywordsSchema

    valid_instance = ArrayKeywordsSchema(
        tags=["python", "pytest"],
        scores=["initial", 95],
    )
    assert valid_instance.tags == ["python", "pytest"]
    assert valid_instance.scores == ["initial", 95]

    # tags minItems violation
    with pytest.raises(e.ArrayLengthViolation):
        ArrayKeywordsSchema(tags=["python"], scores=[95])

    # tags maxItems violation
    with pytest.raises(e.ArrayLengthViolation):
        ArrayKeywordsSchema(tags=["a", "b", "c", "d", "e"], scores=[95])

    # tags uniqueItems violation
    with pytest.raises(e.ArrayUniqueElementViolation):
        ArrayKeywordsSchema(tags=["python", "python"], scores=[95])

    # scores minContains violation
    with pytest.raises(e.ArrayElementViolation):
        ArrayKeywordsSchema(tags=["python", "pytest"], scores=["a", "b"])

    # scores maxContains violation
    with pytest.raises(e.ArrayElementViolation):
        ArrayKeywordsSchema(tags=["python", "pytest"], scores=[10, 20, 30])


@pytest.mark.v2
@pytest.mark.descriptor
def test_object_descriptor():
    ObjSchema = make_dataclass(
        "ObjSchema", [("payload", bases.ObjectDescriptor, bases.ObjectDescriptor())]
    )

    o1 = ObjSchema(payload={"status": "ok"})
    assert o1.payload == {"status": "ok"}

    # Non-dict rejection
    with pytest.raises(e.ValueTypeViolation):
        ObjSchema(payload=[1, 2, 3])

    with pytest.raises(e.ValueTypeViolation):
        ObjSchema(payload="invalid")


@pytest.mark.v2
@pytest.mark.descriptor
def test_null_descriptor():
    NullSchema = make_dataclass(
        "NullSchema",
        [("nothing", bases.NullDescriptor, bases.NullDescriptor(default=None))],
    )

    n1 = NullSchema(nothing=None)
    assert n1.nothing is None

    n_default = NullSchema()
    assert n_default.nothing is None

    # Non-null rejection
    with pytest.raises(e.ValueTypeViolation):
        NullSchema(nothing="not-null")

    with pytest.raises(e.ValueTypeViolation):
        NullSchema(nothing=0)


@pytest.mark.v2
@pytest.mark.descriptor
def test_collection_descriptor():
    CollSchema = make_dataclass(
        "CollSchema",
        [
            (
                "items",
                bases.CollectionDescriptor,
                bases.CollectionDescriptor(metadata={"minLength": 2, "maxLength": 4}),
            )
        ],
    )

    c1 = CollSchema(items=[1, 2, 3])
    assert c1.items == [1, 2, 3]

    # Type violation
    with pytest.raises(e.ValueTypeViolation):
        CollSchema(items=123)

    # Length violation
    with pytest.raises(e.LengthConstraintViolation):
        CollSchema(items=[1])

    with pytest.raises(e.LengthConstraintViolation):
        CollSchema(items=[1, 2, 3, 4, 5])


@pytest.mark.v2
@pytest.mark.descriptor
def test_subschema_constraints():
    # Test allOf, oneOf, not, and anyOf subschemas in JSONSchemaFieldDescriptor
    SubSchemaClass = make_dataclass(
        "SubSchemaClass",
        [
            (
                "all_field",
                bases.StringDescriptor,
                bases.StringDescriptor(
                    metadata={"allOf": [{"minLength": 3}, {"maxLength": 6}]}
                ),
            ),
            (
                "one_field",
                bases.IntegerDescriptor,
                bases.IntegerDescriptor(
                    metadata={"oneOf": [{"minimum": 10}, {"maximum": 5}]}
                ),
            ),
            (
                "not_field",
                bases.NumberDescriptor,
                bases.NumberDescriptor(metadata={"not": {"minimum": 100}}),
            ),
        ],
    )

    inst = SubSchemaClass(all_field="test", one_field=12, not_field=50)
    assert inst.all_field == "test"
    assert inst.one_field == 12
    assert inst.not_field == 50

    # allOf violation
    with pytest.raises(e.SubSchemaFailureViolation):
        SubSchemaClass(all_field="ab", one_field=12, not_field=50)

    # not violation
    with pytest.raises(e.SubSchemaFailureViolation):
        SubSchemaClass(all_field="test", one_field=12, not_field=150)


@pytest.mark.v2
@pytest.mark.descriptor
def test_descriptor_class_access_and_special_keyword():
    desc = bases.StringDescriptor(default="fallback")
    assert desc.__get__(None, object) == "fallback"

    # Test SpecialKeywordDescriptor.process_child_descriptors
    assert (
        bases.SpecialKeywordDescriptor.process_child_descriptors(
            "test_field", str, "hello"
        )
        is True
    )
    assert (
        bases.SpecialKeywordDescriptor.process_child_descriptors("test_field", str, 123)
        is False
    )
    assert (
        bases.SpecialKeywordDescriptor.process_child_descriptors("test_field", int, 123)
        is True
    )
    assert (
        bases.SpecialKeywordDescriptor.process_child_descriptors(
            "test_field", int, "hello"
        )
        is False
    )
    assert (
        bases.SpecialKeywordDescriptor.process_child_descriptors(
            "test_field", bool, True
        )
        is True
    )
    assert (
        bases.SpecialKeywordDescriptor.process_child_descriptors(
            "test_field", bool, "true"
        )
        is False
    )
    assert (
        bases.SpecialKeywordDescriptor.process_child_descriptors(
            "test_field", list, [1, 2]
        )
        is True
    )
    assert (
        bases.SpecialKeywordDescriptor.process_child_descriptors(
            "test_field", list, "not-a-list"
        )
        is False
    )
    assert (
        bases.SpecialKeywordDescriptor.process_child_descriptors(
            "test_field", dict, {"k": "v"}
        )
        is True
    )
    assert (
        bases.SpecialKeywordDescriptor.process_child_descriptors(
            "test_field", dict, [1, 2]
        )
        is False
    )
    assert (
        bases.SpecialKeywordDescriptor.process_child_descriptors(
            "test_field", type(None), None
        )
        is True
    )
    assert (
        bases.SpecialKeywordDescriptor.process_child_descriptors(
            "test_field", type(None), 0
        )
        is False
    )


@pytest.mark.v2
@pytest.mark.descriptor
def test_schema_model_factory_v2_full_model():
    schema = {
        "$id": "https://example.com/user.schema.json",
        "title": "comprehensive-vtwo-user-schema",
        "type": "object",
        "properties": {
            "username": {"type": "string", "minLength": 3, "maxLength": 10},
            "age": {"type": "integer", "minimum": 18},
            "balance": {"type": "number", "minimum": 0.0},
            "is_active": {"type": "boolean", "default": True},
            "notes": {"type": "null", "default": None},
        },
        "required": ["username", "age", "balance"],
    }

    SchemaModelFactoryV2(schemas=[schema])
    from schemamodels.dynamic import ComprehensiveVtwoUserSchema

    user = ComprehensiveVtwoUserSchema(
        username="john_doe", age=25, balance=150.75, is_active=True, notes=None
    )

    assert user.username == "john_doe"
    assert user.age == 25
    assert user.balance == 150.75
    assert user.is_active is True
    assert user.notes is None

    # Test export methods
    d = user.todict()
    assert d["username"] == "john_doe"
    assert d["age"] == 25
    assert "john_doe" in user.tolist()
    csv = user.tocsv(header=True)
    assert "username" in csv
    assert "john_doe" in csv

    # Validation failure on required string length
    with pytest.raises(e.LengthConstraintViolation):
        ComprehensiveVtwoUserSchema(username="jo", age=25, balance=100.0)

    # Validation failure on age range
    with pytest.raises(e.RangeConstraintViolation):
        ComprehensiveVtwoUserSchema(username="john_doe", age=16, balance=100.0)

    # Validation failure on balance type
    with pytest.raises(e.ValueTypeViolation):
        ComprehensiveVtwoUserSchema(username="john_doe", age=25, balance="100.0")


@pytest.mark.v2
@pytest.mark.descriptor
@pytest.mark.multierror
def test_schema_model_factory_v2_multiple_errors():
    schema = {
        "$id": "https://example.com/user.schema.json",
        "title": "comprehensive-vtwo-user-schema",
        "type": "object",
        "properties": {
            "username": {"type": "string", "minLength": 3, "maxLength": 10},
            "age": {"type": "integer", "minimum": 18},
            "balance": {"type": "number", "minimum": 0.0},
            "is_active": {"type": "boolean", "default": True},
            "notes": {"type": "null", "default": None},
        },
        "required": ["username", "age", "balance"],
    }

    SchemaModelFactoryV2(schemas=[schema])
    from schemamodels.dynamic import ComprehensiveVtwoUserSchema

    # Validation failure on required string length
    with pytest.RaisesGroup(e.LengthConstraintViolation, e.RangeConstraintViolation):
        ComprehensiveVtwoUserSchema(username="jo", age=16, balance=100.0)


@pytest.mark.v2
@pytest.mark.descriptor
def test_json_schema_field_descriptor():
    class TestClass:
        field = v2.JSONSchemaFieldDescriptor(
            default="init_val",
            metadata={
                "enum": ["init_val", "other_val"],
                "anyOf": [{"type": "string"}],
            },
        )

    # Class-level access returns default
    assert TestClass.field == "init_val"

    inst = TestClass()
    # Instance-level access before assignment returns default
    assert inst.field == "init_val"

    # Valid assignment
    inst.field = "other_val"
    assert inst.field == "other_val"

    # Enum constraint failure
    with pytest.raises(e.ValueTypeViolation):
        inst.field = "invalid_enum_val"

    # Subschema failure
    class SubschemaTestClass:
        sub_field = v2.JSONSchemaFieldDescriptor(metadata={"allOf": [{"minLength": 5}]})

    sub_inst = SubschemaTestClass()
    with pytest.raises(e.SubSchemaFailureViolation):
        sub_inst.sub_field = "abc"

    # REQUIRED_MISSING failure
    with pytest.raises(e.RequiredPropertyViolation):
        inst.field = REQUIRED_MISSING


@pytest.mark.v2
@pytest.mark.descriptor
def test_special_keyword_descriptor_dynamic_context():
    class CustomSpecialDescriptor(v2.SpecialKeywordDescriptor[str]):
        pass

    class SpecialClass:
        field = CustomSpecialDescriptor(default="initial")

    obj = SpecialClass()
    assert obj.field == "initial"

    desc = SpecialClass.__dict__["field"]
    with desc.dynamic_child_descriptors(obj, "updated_value"):
        pass

    assert obj.field == "updated_value"
    assert desc.__get__(obj) == "updated_value"


@pytest.mark.v2
@pytest.mark.descriptor
@pytest.mark.parametrize(
    "descriptor_cls",
    [
        v2.JSONSchemaFieldDescriptor,
        v2.StringDescriptor,
        v2.IntegerDescriptor,
        v2.NumberDescriptor,
        v2.BooleanDescriptor,
        v2.ArrayDescriptor,
        v2.ObjectDescriptor,
        v2.NullDescriptor,
        v2.CollectionDescriptor,
        v2.SpecialKeywordDescriptor,
    ],
)
def test_all_descriptors_required_missing_handling(descriptor_cls):
    class Container:
        pass

    desc = descriptor_cls()
    desc.__set_name__(Container, "field")
    inst = Container()

    with pytest.raises(e.RequiredPropertyViolation):
        desc.__set__(inst, REQUIRED_MISSING)


@pytest.mark.v2
@pytest.mark.descriptor
def test_standalone_descriptors_fail_fast():
    class StandaloneObj:
        pass

    obj = StandaloneObj()

    # StringDescriptor standalone
    str_desc = v2.StringDescriptor(metadata={"minLength": 4})
    str_desc.__set_name__(StandaloneObj, "s")
    str_desc.__set__(obj, "valid")
    assert obj.s == "valid"
    with pytest.raises(e.LengthConstraintViolation):
        str_desc.__set__(obj, "no")
    with pytest.raises(e.ValueTypeViolation):
        str_desc.__set__(obj, 123)

    # IntegerDescriptor standalone
    int_desc = v2.IntegerDescriptor(metadata={"minimum": 10})
    int_desc.__set_name__(StandaloneObj, "i")
    int_desc.__set__(obj, 15)
    assert obj.i == 15
    with pytest.raises(e.RangeConstraintViolation):
        int_desc.__set__(obj, 5)
    with pytest.raises(e.ValueTypeViolation):
        int_desc.__set__(obj, 15.5)

    # NumberDescriptor standalone
    num_desc = v2.NumberDescriptor(metadata={"maximum": 50.0})
    num_desc.__set_name__(StandaloneObj, "n")
    num_desc.__set__(obj, 25.5)
    assert obj.n == 25.5
    with pytest.raises(e.RangeConstraintViolation):
        num_desc.__set__(obj, 75.0)

    # BooleanDescriptor standalone
    bool_desc = v2.BooleanDescriptor()
    bool_desc.__set_name__(StandaloneObj, "b")
    bool_desc.__set__(obj, True)
    assert obj.b is True
    with pytest.raises(e.ValueTypeViolation):
        bool_desc.__set__(obj, "true")

    # ArrayDescriptor standalone
    arr_desc = v2.ArrayDescriptor()
    arr_desc.__set_name__(StandaloneObj, "a")
    arr_desc.__set__(obj, [1, 2])
    assert obj.a == [1, 2]
    arr_desc.__set__(obj, (3, 4))
    assert obj.a == (3, 4)
    with pytest.raises(e.ValueTypeViolation):
        arr_desc.__set__(obj, "1,2")

    # ObjectDescriptor standalone
    obj_desc = v2.ObjectDescriptor()
    obj_desc.__set_name__(StandaloneObj, "o")
    obj_desc.__set__(obj, {"key": "val"})
    assert obj.o == {"key": "val"}
    with pytest.raises(e.ValueTypeViolation):
        obj_desc.__set__(obj, [1, 2])

    # NullDescriptor standalone
    null_desc = v2.NullDescriptor()
    null_desc.__set_name__(StandaloneObj, "nl")
    null_desc.__set__(obj, None)
    assert obj.nl is None
    with pytest.raises(e.ValueTypeViolation):
        null_desc.__set__(obj, 0)

    # CollectionDescriptor standalone
    col_desc = v2.CollectionDescriptor(metadata={"maxLength": 2})
    col_desc.__set_name__(StandaloneObj, "c")
    col_desc.__set__(obj, (1, 2))
    assert obj.c == (1, 2)
    with pytest.raises(e.LengthConstraintViolation):
        col_desc.__set__(obj, [1, 2, 3])


@pytest.mark.v2
@pytest.mark.descriptor
def test_v2_exports_and_parity():
    expected_descriptors = {
        "ArrayDescriptor",
        "BooleanDescriptor",
        "CollectionDescriptor",
        "IntegerDescriptor",
        "JSONSchemaFieldDescriptor",
        "NullDescriptor",
        "NumberDescriptor",
        "ObjectDescriptor",
        "SpecialKeywordDescriptor",
        "StringDescriptor",
    }
    assert expected_descriptors.issubset(set(v2.__all__))

    for name in expected_descriptors:
        v2_cls = getattr(v2, name)
        bases_cls = getattr(bases, name)
        assert v2_cls is bases_cls


@pytest.mark.v2
@pytest.mark.descriptor
def test_all_descriptors_comparisons():
    descriptor_classes = [
        v2.JSONSchemaFieldDescriptor,
        v2.ArrayDescriptor,
        v2.BooleanDescriptor,
        v2.CollectionDescriptor,
        v2.IntegerDescriptor,
        v2.NullDescriptor,
        v2.NumberDescriptor,
        v2.ObjectDescriptor,
        v2.SpecialKeywordDescriptor,
        v2.StringDescriptor,
    ]
    for desc_cls in descriptor_classes:
        assert hasattr(desc_cls, "COMPARISONS")
        assert isinstance(desc_cls.COMPARISONS, dict)

    assert set(v2.StringDescriptor.COMPARISONS.keys()) == {
        "maxLength",
        "minLength",
        "format",
    }
    assert set(v2.IntegerDescriptor.COMPARISONS.keys()) == {
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "multipleOf",
    }
    assert set(v2.NumberDescriptor.COMPARISONS.keys()) == {
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "multipleOf",
    }
    assert set(v2.CollectionDescriptor.COMPARISONS.keys()) == {
        "maxLength",
        "minLength",
    }
    assert set(v2.ArrayDescriptor.COMPARISONS.keys()) == {
        "maxItems",
        "minItems",
        "maxContains",
        "minContains",
        "uniqueItems",
    }
    assert v2.BooleanDescriptor.COMPARISONS == {}
    assert v2.ObjectDescriptor.COMPARISONS == {}
    assert v2.NullDescriptor.COMPARISONS == {}
    assert v2.SpecialKeywordDescriptor.COMPARISONS == {}
    assert v2.JSONSchemaFieldDescriptor.COMPARISONS == {}
