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


@pytest.mark.struct
def test_required_keyword_schema_validation(Factory):
    sm = Factory()

    # Valid required keyword (array of unique strings)
    valid_schema = {
        "title": "valid-required-schema",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
        },
        "required": ["name", "age"],
    }
    assert sm.register(valid_schema)

    # Empty array is valid per JSON Schema specification
    empty_req_schema = {
        "title": "empty-required-schema",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
        },
        "required": [],
    }
    assert sm.register(empty_req_schema)

    # Malformed: required is not an array (string)
    invalid_string_req = {
        "title": "invalid-req-1",
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": "name",
    }
    with pytest.raises(exceptions.MalformedSchemaViolation):
        sm.register(invalid_string_req)

    # Malformed: required is not an array (dict)
    invalid_dict_req = {
        "title": "invalid-req-2",
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": {"name": True},
    }
    with pytest.raises(exceptions.MalformedSchemaViolation):
        sm.register(invalid_dict_req)

    # Malformed: required contains non-strings
    invalid_elements_req = {
        "title": "invalid-req-3",
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": [123],
    }
    with pytest.raises(exceptions.MalformedSchemaViolation):
        sm.register(invalid_elements_req)

    # Malformed: required contains duplicate strings
    invalid_duplicates_req = {
        "title": "invalid-req-4",
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name", "name"],
    }
    with pytest.raises(exceptions.MalformedSchemaViolation):
        sm.register(invalid_duplicates_req)


@pytest.mark.struct
def test_required_keyword_runtime_enforcement(Factory):
    sm = Factory()

    schema = {
        "title": "multi-req-enforcement-schema",
        "type": "object",
        "properties": {
            "username": {"type": "string", "minLength": 3},
            "email": {"type": "string"},
            "age": {"type": "integer", "minimum": 18},
            "status": {"type": "string", "default": "active"},
        },
        "required": ["username", "email", "status"],
    }
    sm.register(schema)

    from schemamodels.dynamic import MultiReqEnforcementSchema

    # 1. Valid instance with all required provided and status using default
    instance = MultiReqEnforcementSchema(
        username="john_doe", email="john@example.com", age=25
    )
    assert instance.username == "john_doe"
    assert instance.email == "john@example.com"
    assert instance.age == 25
    assert instance.status == "active"

    # 2. Missing single required field raises RequiredPropertyViolation
    with pytest.raises(exceptions.RequiredPropertyViolation):
        MultiReqEnforcementSchema(email="john@example.com", age=25)

    with pytest.raises(exceptions.RequiredPropertyViolation):
        MultiReqEnforcementSchema(username="john_doe", age=25)

    # 3. Missing multiple required fields raises ExceptionGroup
    with pytest.raises(ExceptionGroup) as exc_info:
        MultiReqEnforcementSchema(age=25)
    assert len(exc_info.value.exceptions) == 2
    for err in exc_info.value.exceptions:
        assert isinstance(err, exceptions.RequiredPropertyViolation)

    # 4. Missing required field AND constraint violation raises ExceptionGroup with both
    with pytest.raises(ExceptionGroup) as exc_info:
        MultiReqEnforcementSchema(
            username="jo", age=16
        )  # missing email, minLength fails, minimum fails
    assert len(exc_info.value.exceptions) >= 2
    err_types = {type(err) for err in exc_info.value.exceptions}
    assert exceptions.RequiredPropertyViolation in err_types
    assert exceptions.LengthConstraintViolation in err_types


@pytest.mark.struct
def test_missing_required_keyword_means_all_fields_required(Factory):
    sm = Factory()

    schema = {
        "title": "missing-required-kw-schema",
        "type": "object",
        "properties": {
            "first_name": {"type": "string"},
            "last_name": {"type": "string"},
            "age": {"type": "integer"},
            "role": {"type": "string", "default": "member"},
        },
    }
    sm.register(schema)

    from schemamodels.dynamic import MissingRequiredKwSchema

    # 1. Valid instance with all non-default fields provided and role taking default
    instance = MissingRequiredKwSchema(first_name="Ada", last_name="Lovelace", age=36)
    assert instance.first_name == "Ada"
    assert instance.last_name == "Lovelace"
    assert instance.age == 36
    assert instance.role == "member"

    # 2. Missing one required field (since all fields without defaults are required when 'required' keyword is absent)
    with pytest.raises(exceptions.RequiredPropertyViolation):
        MissingRequiredKwSchema(first_name="Ada", last_name="Lovelace")  # missing age

    with pytest.raises(exceptions.RequiredPropertyViolation):
        MissingRequiredKwSchema(first_name="Ada", age=36)  # missing last_name

    # 3. Missing multiple required fields raises ExceptionGroup
    with pytest.raises(ExceptionGroup) as exc_info:
        MissingRequiredKwSchema()
    assert len(exc_info.value.exceptions) == 3
    for err in exc_info.value.exceptions:
        assert isinstance(err, exceptions.RequiredPropertyViolation)
