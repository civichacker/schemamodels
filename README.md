<!--
SPDX-FileCopyrightText: 2023 Civic Hacker, LLC

SPDX-License-Identifier: GPL-3.0-or-later
-->

# Schema Models

![PyPI](https://img.shields.io/pypi/v/schemamodels?style=for-the-badge) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/schemamodels?style=for-the-badge)
[![REUSE status](https://api.reuse.software/badge/git.fsfe.org/reuse/api)](https://api.reuse.software/info/git.fsfe.org/reuse/api)

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

### Faster than defining dataclasses manually

The class-like syntax of creating dataclasses is a useful way to model a valid JSON schema. This library essentially makes your existing JSON schemas usable as a Python dataclass.

### Useable everywhere

Taking the time to construct a plain ol' Pythjon dataclass, ensures widespread utility across of multiple domains of study and applications.

### Just-enough validation

The dataclasses are not completely dumb. Every dataclass _object_ that originated from a valid JSON schema, will perform runtime checks on the input you provide it.

These basic checks are performed _every time_ you create a new instance of a generated dataclass:

- Are the field names correct?
- Are the required fields present?
- Does the input match the datatype expectations set forth by the generated dataclass?

## License

This codebase is licensed under the GPLv3+ and therefore the use, inclusion, modification, and distribution of this software is governed by the GPL.

To opt-out of the obligations of the GPL, inquire about the commercial license by sending an email to: license@civichacker.com.
