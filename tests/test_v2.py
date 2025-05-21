import sys
from jsonschema import validators
import json
import importlib
from dataclasses import make_dataclass, FrozenInstanceError, dataclass

from schemamodels import SchemaModelFactory, SchemaModelFactoryV2, exceptions, bases, COMPARISONS
from schemamodels import generate_functors

from schemamodels import v2, bases
from schemamodels import exceptions as e
from typing import TypeVar, Generic, runtime_checkable, get_args, get_origin
import types


from functools import partialmethod
from contextlib import contextmanager


import pytest

T = TypeVar('T', str, int, float, bool, None)
C = TypeVar('C', list, tuple)
A = TypeVar('A')




@pytest.mark.v2
def test_new_iterable(simple_schema):

    obj_gen = v2.process_keys(simple_schema)
    for k in obj_gen:
        assert k in simple_schema.get('properties').keys()

@pytest.mark.v2
def test_scalar_descriptor(simple_schema):

    SimpleSchema = make_dataclass(
        'SimpleSchema',
        [
            ('name', bases.StringDescriptor, bases.StringDescriptor(metadata={'maxLength': 3})),
            ('id', bases.NumberDescriptor, bases.NumberDescriptor())
        ]

    )

    ss = SimpleSchema(name="nic", id=2)

    with pytest.raises(e.LengthConstraintViolation):
        SimpleSchema(name="nice", id="nice")

@pytest.mark.anyof
@pytest.mark.v2
def test_anyof_descriptor(anyof_schema):

    passed_in_types = [int, float]

    AnyOfDescriptor = SchemaModelFactoryV2.dynamic_descriptor(passed_in_types)

    AnyOfSchema = make_dataclass(
        'AnyOfSchema',
        [
            ('brand_name', bases.StringDescriptor, bases.StringDescriptor(metadata={'maxLength': 3})),
            ('provider_id', AnyOfDescriptor, AnyOfDescriptor())
        ]

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
    passed_in_types = [int, str] # Drives the tyoe check

    AnyOfDescriptor = SchemaModelFactoryV2.dynamic_descriptor(passed_in_types)
    # Act
    AnyOfSchema = make_dataclass(
        'AnyOfSchema',
        [
            ('provider_id', AnyOfDescriptor, AnyOfDescriptor()),
        ] + [
            ('brand_name', bases.StringDescriptor, bases.StringDescriptor(metadata={'maxLength': 3})),
        ]

    )

    # Test
    assert AnyOfSchema(brand_name="nic", provider_id=2)

    assert AnyOfSchema(brand_name="nic", provider_id="str")

    with pytest.raises(e.LengthConstraintViolation):
        AnyOfSchema(brand_name="nice", provider_id=2)

    with pytest.raises(e.ValueTypeViolation):
        AnyOfSchema(brand_name="nic", provider_id=3.2)
