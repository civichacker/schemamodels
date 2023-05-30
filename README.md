# Schema Models

![PyPI](https://img.shields.io/pypi/v/schemamodels?style=for-the-badge) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/schemamodels?style=for-the-badge)

Use this library to turn a JSON Schema into a plain 'ol Python dataclass.

## Installation

Install this package using the usual suspects.

```
pip install schemamodels
```

## Usage

This library **only** supports JSON schemas of `type: object`:

```json
    {
        "$id": "https://schema.dev/fake-schema.schema.json",
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "fake-schema",
        "description": "Blue Blah",
        "type": "object",
        "properties": {
            "property_a": {
              "default": 5,
              "type": "integer"
            },
            "property_b": {
              "type": "string"
            }
        }
    }
```

```python
from schemamodels import SchemaModelFactory

schema_string = '..'
my_json_schema = json.loads(schema_string)

factory = SchemaModelFactory()
factory.register(my_json_schema)
```


Use your new dataclass

```python
from schemamodels import exceptions
from schemamodels.dynamic import FakeSchema

your_data_instance = FakeSchema(property_a=2334)  # OK

with pytest.raises(exceptions.ValueTypeViolation):
  your_data_instance = FakeSchema(property_a="hello")

```

## Why this library exists

### The JSON Schema can come from anywhere

Regardless of where your JSON schema originated, it only needs to be valid for the Draft version you care about. There are a number of libraries better suited validating a JSON Schema document. A user of this library would obtain a JSON Schema document using their prefered method (filesystem, remote), then pass it to this library.


### Just-enough validation

Use this library, if there are some basic checks you'd like performed _every time_ create a new instance data class. Also, questions about the quality of the data is out of scope.

I want to have the confidence that the data has a structure the adhears to the rules provided by a JSON Schema.

I want to be sure that the dictionary exported by these data classes would pass validation checks. The specific tool used to validate an instance of data against the original JSON Schema shouldn't matter.

### I'm tired of writing Python classes by hand

While I like using classes to write Python declaratively, I think letting JSON Schema drive the data models creates an opportunity to automate.

When I have a valid JSON Schema, I can create a new Python dataclass with one line of code.


## License

This codebase is licensed under the GPLv3+ and therefore the use, inclusion, modification, and distribution of this software is governed by the GPL.

If you are planning to use schemamodels in a commercial product or wish to opt-out of the obligations of the GPL, please reach out to license@civichacker.com.
