
from jsonschema import validators
import json
import importlib
from dataclasses import make_dataclass, FrozenInstanceError, dataclass

from schemamodels import SchemaModelFactory, SchemaModelFactoryV2, exceptions, bases, COMPARISONS
from schemamodels import generate_functors

from schemamodels import v2, bases
from schemamodels import exceptions as e
from typing import TypeVar, Generic, runtime_checkable, get_args, get_origin


import pytest

T = TypeVar('T', str, int, float, bool, None)
C = TypeVar('C', list, tuple)




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

    SimpleSchema(name="nic", id=2)

    with pytest.raises(e.LengthConstraintViolation):
        SimpleSchema(name="nice", id="nice")
