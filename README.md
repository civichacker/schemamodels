## Schema Models

Dynamically created data classes from JSON schemas


Use this library to quickly turn a JSON Schema and turn into a Python dataclass that you can immediately consume.


## Installation

Install this package using the usual suspects.

```
pip install schemamodels
```

## Usage

Assuming you have a JSON schema like:

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


factory = SchemaModelFactory()

schema_string = '..'

my_json_schema = json.loads(schema_string)

factory.register(my_json_schema)
```


Use your new dataclass

```python
from schemamodels.dynamic import FakeSchema

your_data_instance = FakeSchema(property_a="hello")

```

## Rationale

### The JSON Schema can come from anywhere

Regardless of where the JSON schema originated, it only needs to be valid for the Draft version you care about. There are a number of libraries better suited validating a JSON Schema document. A user of this library would obtain a JSON Schema document using their prefered method (filesystem, remote), then pass it to this library.


### Just-enough validation

At this time, I'm not interested in validating a JSON Schema. However, there are some basic checks I'd like to have performed _every time_ create a new instance of a object that's designed to _hold_ my data. Also, questions about the quality of the data is out of scope.

I want to have the confidence that the data has a structure the adhears to the rules provided by a JSON Schema.

I want to be sure that the dictionary exported by these data classes would pass validation checks. The specific tool used to validate an instance of data against the original JSON Schema shouldn't matter.

### I'm tired of writing Python classes by hand

While I like using Python-classes to write Python declaratively, I think letting JSON Schema drive the data models creates an opportunity to automate.

When I have a valid JSON Schema, I can create a new Python dataclass with zero or one-line of code.
