from schemamodels import utils


def test_generate_classname():
    assert utils.generate_classname("tell-tail") == "TellTail"


def test_detect_schema_object(simple_schema, malformed_schema):
    assert utils.is_schema_object(simple_schema)
    assert not utils.is_schema_object(malformed_schema)
