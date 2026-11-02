# SPDX-FileCopyrightText: 2023-2026 Civic Hacker LLC
# SPDX-License-Identifier: GPL-3.0-or-later
from typing import Generic, TypeVar

from schemamodels import exceptions as e
from schemamodels.bases import (
    ArrayDescriptor,
    BooleanDescriptor,
    IntegerDescriptor,
    JSONSchemaFieldDescriptor,
    NullDescriptor,
    NumberDescriptor,
    ObjectDescriptor,
    SpecialKeywordDescriptor,
    StringDescriptor,
)
from schemamodels.bases import (
    CollectionDescriptor as BaseCollectionDescriptor,
)

T = TypeVar("T", bound=str)


def process_keys(structure: dict):
    yield from set(structure.get("properties", {}).keys()) - {"$id", "$schema"}


class CollectionDescriptor(Generic[T]):
    def __init__(self, *, default=None, metadata=dict):
        self._metadata = metadata
        self._default = default

    def __set_name__(self, o, name):
        self._name = "_" + name

    def __set__(self, obj, value: T):
        if not isinstance(value, list):
            raise e.ValueTypeViolation()
        setattr(obj, self._name, value)


__all__ = [
    "ArrayDescriptor",
    "BaseCollectionDescriptor",
    "BooleanDescriptor",
    "CollectionDescriptor",
    "IntegerDescriptor",
    "JSONSchemaFieldDescriptor",
    "NullDescriptor",
    "NumberDescriptor",
    "ObjectDescriptor",
    "SpecialKeywordDescriptor",
    "StringDescriptor",
    "process_keys",
]
