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
    l = user.tolist()
    assert "john_doe" in l
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
        sub_field = v2.JSONSchemaFieldDescriptor(
            metadata={"allOf": [{"minLength": 5}]}
        )

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
