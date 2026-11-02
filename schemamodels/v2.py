# SPDX-FileCopyrightText: 2023-2026 Civic Hacker LLC
# SPDX-License-Identifier: GPL-3.0-or-later
from typing import TypeVar

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
    CollectionDescriptor,
)

T = TypeVar("T", bound=str)


def process_keys(structure: dict):
    yield from set(structure.get("properties", {}).keys()) - {"$id", "$schema"}


__all__ = [
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
    "process_keys",
]
