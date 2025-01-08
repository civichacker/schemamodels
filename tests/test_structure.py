import pytest
from schemamodels import SchemaModelFactory, exceptions, bases, COMPARISONS
from schemamodels import generate_functors, utils


@pytest.mark.struct
def test_is_object(simple_schema):
    assert utils.is_schema_object(simple_schema)


@pytest.mark.struct
def test_is_not_object(malformed_schema):
    assert not utils.is_schema_object(malformed_schema)


@pytest.mark.struct
def test_raise_on_malformed_schema(malformed_schema):
    assert not utils.is_schema_object(malformed_schema)
    sm = SchemaModelFactory()

    with pytest.raises(exceptions.MalformedSchemaViolation):
        sm.register(malformed_schema)


@pytest.mark.struct
def test_simple_new_processor(simple_schema):
    sm = SchemaModelFactory()

    sm.register(simple_schema)
