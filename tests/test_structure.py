# SPDX-FileCopyrightText: 2023-2026 Civic Hacker LLC
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest

from schemamodels import exceptions, utils


@pytest.mark.struct
def test_is_object(simple_schema, Factory):
    assert utils.is_schema_toplevel_object(simple_schema)


@pytest.mark.struct
def test_is_not_object(malformed_schema):
    assert not utils.is_schema_toplevel_object(malformed_schema)


@pytest.mark.struct
def test_raise_on_malformed_schema(malformed_schema, Factory):
    assert not utils.is_schema_toplevel_object(malformed_schema)
    sm = Factory()

    with pytest.raises(exceptions.MalformedSchemaViolation):
        sm.register(malformed_schema)


@pytest.mark.struct
def test_simple_new_processor(simple_schema, Factory):
    sm = Factory()

    sm.register(simple_schema)
