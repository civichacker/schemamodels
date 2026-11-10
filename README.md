<!--
SPDX-FileCopyrightText: 2023 Civic Hacker LLC

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

schema_string = ".."
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

### Required Fields Behavior

> **Design Decision Note**:
> In standard JSON Schema specifications, object properties are optional by default unless explicitly listed in the `required` array (see [Understanding JSON Schema: required](https://json-schema.org/understanding-json-schema/reference/object#required)).
>
> In `schemamodels`, **a missing `required` keyword means that all fields are required**. When registering an object schema without a `required` keyword, all defined properties without explicit `default` values become required fields.
>
> To make fields optional, either:
> - Explicitly define the `required` keyword with only the mandatory properties (e.g., `"required": ["property_a"]` or `"required": []` to make all fields optional).
> - Specify an explicit `"default"` value on the property definition.

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

## JSON Schema 2020-12 Structural Validation Support

Below is the current support status for the keywords defined in [Section 6 (A Vocabulary for Structural Validation)](https://json-schema.org/draft/2020-12/json-schema-validation#name-a-vocabulary-for-structural) of the JSON Schema 2020-12 specification:

| Keyword | Section | Category | Supported |
| --- | --- | --- | --- |
| `type` | 6.1.1 | Any Instance Type | ✅ |
| `enum` | 6.1.2 | Any Instance Type | ✅ |
| `const` | 6.1.3 | Any Instance Type | ❌ |
| `multipleOf` | 6.2.1 | Numeric Instances | ✅ |
| `maximum` | 6.2.2 | Numeric Instances | ✅ |
| `exclusiveMaximum` | 6.2.3 | Numeric Instances | ✅ |
| `minimum` | 6.2.4 | Numeric Instances | ✅ |
| `exclusiveMinimum` | 6.2.5 | Numeric Instances | ✅ |
| `maxLength` | 6.3.1 | String Instances | ✅ |
| `minLength` | 6.3.2 | String Instances | ✅ |
| `pattern` | 6.3.3 | String Instances | ❌ |
| `maxItems` | 6.4.1 | Array Instances | ❌ |
| `minItems` | 6.4.2 | Array Instances | ❌ |
| `uniqueItems` | 6.4.3 | Array Instances | ❌ |
| `maxContains` | 6.4.4 | Array Instances | ❌ |
| `minContains` | 6.4.5 | Array Instances | ❌ |
| `maxProperties` | 6.5.1 | Object Instances | ❌ |
| `minProperties` | 6.5.2 | Object Instances | ❌ |
| `required` | 6.5.3 | Object Instances | ✅ |
| `dependentRequired` | 6.5.4 | Object Instances | ❌ |

## JSON Schema 2020-12 String Format Support

Below is the current support status for the string `format` keywords defined in [Section 7.3 (Defined Formats)](https://json-schema.org/draft/2020-12/json-schema-validation#name-defined-formats) of the JSON Schema 2020-12 specification:

| Format | Section | Category | Supported |
| --- | --- | --- | --- |
| `date-time` | 7.3.1 | Dates, Times, and Duration | ✅ |
| `date` | 7.3.1 | Dates, Times, and Duration | ✅ |
| `time` | 7.3.1 | Dates, Times, and Duration | ✅ |
| `duration` | 7.3.1 | Dates, Times, and Duration | ✅ |
| `email` | 7.3.2 | Email Addresses | ✅ |
| `idn-email` | 7.3.2 | Email Addresses | ❌ |
| `hostname` | 7.3.3 | Hostnames | ✅ |
| `idn-hostname` | 7.3.3 | Hostnames | ❌ |
| `ipv4` | 7.3.4 | IP Addresses | ✅ |
| `ipv6` | 7.3.4 | IP Addresses | ✅ |
| `uri` | 7.3.5 | Resource Identifiers | ✅ |
| `uri-reference` | 7.3.5 | Resource Identifiers | ✅ |
| `iri` | 7.3.5 | Resource Identifiers | ✅ |
| `iri-reference` | 7.3.5 | Resource Identifiers | ✅ |
| `uuid` | 7.3.5 | Resource Identifiers | ✅ |
| `uri-template` | 7.3.6 | URI Template | ❌ |
| `json-pointer` | 7.3.7 | JSON Pointers | ❌ |
| `relative-json-pointer` | 7.3.7 | JSON Pointers | ❌ |
| `regex` | 7.3.8 | Regular Expressions | ❌ |

## Benchmark Overview

The performance benchmark evaluates `SchemaModelFactory` (V1, based on functor dispatch and metaprogramming) against `SchemaModelFactoryV2` (V2, based on the descriptor pattern for structural validation) across 4 schema workloads (`customer_record`, `ecommerce_order`, `sensor_telemetry`, and `simple_user`) with 10,000 iterations per workload.

## Benchmark Comparison

### Python 3.12.3 Execution Metrics

| Phase | V1 Time (s) | V2 Time (s) | Speedup |
| --- | --- | --- | --- |
| Registration | 0.008996 | 0.007591 | 1.19x |
| Instantiation & Validate | 0.774447 | 0.302700 | 2.56x |
| **Total Time** | **0.783443** | **0.310291** | **2.52x** |

### Python 3.15.2 Execution Metrics

| Phase | V1 Time (s) | V2 Time (s) | Speedup |
| --- | --- | --- | --- |
| Registration | 0.011681 | 0.005333 | 2.19x |
| Instantiation & Validate | 0.655611 | 0.225569 | 2.91x |
| **Total Time** | **0.667292** | **0.230902** | **2.89x** |

## License

This codebase is licensed under the GPLv3+ and therefore the use, inclusion, modification, and distribution of this software is governed by the GPL.

To opt-out of the obligations of the GPL, inquire about the commercial license by sending an email to: license AT civichacker.com.
