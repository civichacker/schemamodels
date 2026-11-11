# SPDX-FileCopyrightText: 2023-2026 Civic Hacker LLC
# SPDX-License-Identifier: GPL-3.0-or-later

import importlib
from collections import deque
from collections.abc import Callable
from dataclasses import Field, asdict, field, make_dataclass
from dataclasses import fields as fs
from functools import partial, reduce
from operator import not_, xor
from typing import ClassVar, TypeVar

from schemamodels import bases, exceptions, utils, v2
from schemamodels import exceptions as e
from schemamodels.bases import BaseErrorHandler, BaseRenderer
from schemamodels.constants import (
    COMPARISONS,
    DEFAULT_FACTORIES,
    JSON_TYPE_MAP,
    PORCELINE_KEYWORDS,
    REQUIRED_MISSING,
)

__all__ = [
    "COMPARISONS",
    "DEFAULT_FACTORIES",
    "JSON_TYPE_MAP",
    "PORCELINE_KEYWORDS",
    "REQUIRED_MISSING",
    "DefaultErrorHandler",
    "DefaultRenderer",
    "SchemaModelFactory",
    "SchemaModelFactoryV2",
    "bases",
    "exceptions",
    "functor_eval",
    "generate_functors",
    "process_functors",
    "utils",
    "v2",
]


class DefaultErrorHandler(bases.BaseErrorHandler):
    ERROR_MAP: ClassVar[dict] = {
        "not": (e.SubSchemaFailureViolation, "subschema failed"),
        "oneOf": (
            e.SubSchemaFailureViolation,
            "none or multiple of the subschemas failed",
        ),
        "anyOf": (e.SubSchemaFailureViolation, "all of the subschemas failed"),
        "allOf": (e.SubSchemaFailureViolation, "at least one subschema failed"),
        "type": (e.ValueTypeViolation, "incorrect type assigned to JSON property"),
        "enum": (e.ValueTypeViolation, "string property much use declared enum values"),
        "maximum": (e.RangeConstraintViolation, "violates range constraint"),
        "exclusiveMaximum": (e.RangeConstraintViolation, "violates range constraint"),
        "exclusiveMinimum": (e.RangeConstraintViolation, "violates range constraint"),
        "minimum": (e.RangeConstraintViolation, "violates range constraint"),
        "multipleOf": (e.RangeConstraintViolation, "violates range constraint"),
        "maxLength": (e.LengthConstraintViolation, "violates length constraint"),
        "minLength": (e.LengthConstraintViolation, "violates length constraint"),
        "maxItems": (e.ArrayLengthViolation, "violates array length constraint"),
        "minItems": (e.ArrayLengthViolation, "violates array length constraint"),
        "uniqueItems": (
            e.ArrayUniqueElementViolation,
            "violates array unique element constraint",
        ),
        "contains": (e.ArrayElementViolation, "violates array element constraint"),
        "minContains": (e.ArrayElementViolation, "violates array element constraint"),
        "maxContains": (e.ArrayElementViolation, "violates array element constraint"),
    }

    @classmethod
    def apply(cls, instance: object) -> object:
        errors = []
        for f in fs(instance):
            val = getattr(instance, f.name)
            if val is REQUIRED_MISSING:
                errors.append(
                    e.RequiredPropertyViolation(f"{f.name} is a required property")
                )

        fields_with_metadata = [
            f
            for f in fs(instance)
            if f.metadata != {} and getattr(instance, f.name) is not REQUIRED_MISSING
        ]
        final_form = [
            {"value": getattr(instance, f.name), "name": f.name, "metadata": f.metadata}
            for f in fields_with_metadata
        ]

        nodes = process_functors(final_form)

        for n in nodes:
            for k, valid in n.items():
                if not valid and k in cls.ERROR_MAP:
                    err_cls, msg = cls.ERROR_MAP[k]
                    errors.append(err_cls(msg))

        if len(errors) == 1:
            raise errors[0]
        if len(errors) > 1:
            raise ExceptionGroup("Validation errors", errors)

        return instance


class DefaultRenderer(bases.BaseRenderer):
    @classmethod
    def apply(cls, instance: object) -> object:
        return instance


def generate_functors(struct):
    o = {k: COMPARISONS[k](v) for k, v in struct.items() if k not in PORCELINE_KEYWORDS}
    if "contains" in struct:
        contains_sub = struct["contains"]
        min_c = struct.get("minContains", 1)
        max_c = struct.get("maxContains")

        def _contains_check(v):
            if not isinstance(v, (list, tuple)):
                return True
            matches = sum(
                1 for item in v if utils.validate_subschema(contains_sub, item)
            )
            if matches < min_c:
                return False
            if max_c is not None and matches > max_c:
                return False
            return True

        o["contains"] = _contains_check
    return bases.CoreModel(o)


def process_functors(nodes):
    t = []
    for node in nodes:
        for k, v in node["metadata"].items():
            if k == "anyOf":
                ans_list = v(node["value"])
                t.append({k: any(all(m.values()) for m in ans_list)})
            elif k == "allOf":
                ans_list = v(node["value"])
                t.append({k: all(all(m.values()) for m in ans_list)})
            elif k == "oneOf":
                ans_list = v(node["value"])
                t.append({k: reduce(xor, [all(m.values()) for m in ans_list])})
            elif k == "not":
                ans_list = [fun(node["value"]) for fun in v.values()]
                t.append({k: not_(all(ans_list))})
            else:
                ans_list = v(node["value"])
                t.append({k: ans_list})
    return t


def functor_eval(functors: Callable, value):
    return [{f: func[f](value) for f in func} for func in functors]


class SchemaModelFactory:
    def __init__(
        self, schemas=None, error_handler=DefaultErrorHandler, renderer=DefaultRenderer
    ):
        if schemas is None:
            schemas = []
        self.error_handler = error_handler
        self.renderer = renderer
        self.___check_custom_hooks()
        self.dmod = importlib.import_module("schemamodels.dynamic")
        [
            self.register(s) for s in schemas
        ]  # FIXME: find another way to 'process' the map

    def ___check_custom_hooks(self):
        self.error_handler()
        self.renderer()

    def construct_dataclass(
        self, klassname: str, schema: dict, fields: deque, fields_with_defaults: deque
    ) -> Callable:
        return partial(
            make_dataclass,
            klassname,
            fields + fields_with_defaults,
            frozen=True,
            namespace={
                "_errorhandler": self.error_handler.apply,
                "_renderer": self.renderer.apply,
                "tocsv": lambda self, header=False, fields=schema["properties"].keys(): (  # noqa: B008
                    f"{','.join(fields)}\n{','.join(asdict(self)[i] for i in fields)}"
                    if header
                    else ",".join(asdict(self)[i] for i in fields)
                ),
                "tolist": lambda self: list(asdict(self).values()),
                "todict": lambda self: asdict(self),
                "__post_init__": lambda self: self._errorhandler(self)._renderer(self),
            },
        )

    def process_subschema(self, subschema: str, values: dict) -> dict:
        funcs = [generate_functors(s) for s in values[subschema]]
        return {subschema: partial(functor_eval, funcs)}

    def process_object(  # noqa: C901
        self, schema: dict, required_fields: list | None = None
    ) -> tuple:
        if required_fields is None:
            if "required" in schema:
                req = schema["required"]
                required_fields = (
                    list(req) if isinstance(req, (list, tuple, set)) else []
                )
            else:
                required_fields = list(schema.get("properties", {}).keys())
        else:
            required_fields = (
                list(required_fields)
                if isinstance(required_fields, (list, tuple, set))
                else []
            )
        fields = deque()
        fields_with_defaults = deque()
        for k, v in schema["properties"].items():
            field_spec = {}
            field_meta = {}
            entry = (k,)

            if "anyOf" in v:
                field_meta.update(self.process_subschema("anyOf", v))
            if "oneOf" in v:
                field_meta.update(self.process_subschema("oneOf", v))
            if "allOf" in v:
                field_meta.update(self.process_subschema("allOf", v))
            if "not" in v:
                field_meta.update({"not": generate_functors(v.get("not"))})

            if v.get("type", None) and v.get("type") != "object":
                entry += (JSON_TYPE_MAP.get(v.get("type")),)
                field_spec.update(default_factory=DEFAULT_FACTORIES[v.get("type")])
            elif v.get("type") == "object":
                fs, _ = self.process_object(v.get("properties"))
                entry += (k, fs)
                field_spec.update(default_factory=DEFAULT_FACTORIES[v.get("type")])
            else:
                print("not a built-in")
                entry += (1,)

            if "default" in v:
                field_spec.update(default=v.get("default", Field))
                field_spec.pop("default_factory", None)
            elif k in required_fields:
                field_spec.update(default=REQUIRED_MISSING)
                field_spec.pop("default_factory", None)
            else:
                field_spec.update(
                    default_factory=DEFAULT_FACTORIES.get(v.get("type"), str)
                )

            field_meta.update(generate_functors(v))
            field_spec.update(metadata=field_meta)

            entry += (field(**field_spec),)
            fields.append(entry)

        return (fields, fields_with_defaults)

    def register(self, schema: dict) -> bool:
        if not utils.is_schema_toplevel_object(schema):
            raise e.MalformedSchemaViolation()

        if "required" in schema:
            req = schema["required"]
            if (
                not isinstance(req, list)
                or not all(isinstance(x, str) for x in req)
                or len(req) != len(set(req))
            ):
                raise e.MalformedSchemaViolation(
                    "required keyword must be an array of unique strings"
                )
            required_fields = schema.get("required", [])
        else:
            required_fields = list(schema.get("properties", {}).keys())

        klassname = utils.generate_classname(schema.get("title"))

        fields, fields_with_defaults = self.process_object(
            schema, required_fields=required_fields
        )
        dklass = self.construct_dataclass(
            klassname, schema, fields, fields_with_defaults
        )
        dataklass = dklass(slots=True)
        setattr(self.dmod, klassname, dataklass)
        return True


class SchemaModelFactoryV2(SchemaModelFactory):
    MAP_TTYPE: ClassVar[dict] = {
        "string": bases.StringDescriptor,
        "number": bases.NumberDescriptor,
        "integer": bases.IntegerDescriptor,
        "boolean": bases.BooleanDescriptor,
        "array": bases.ArrayDescriptor,
        "object": bases.ObjectDescriptor,
        "null": bases.NullDescriptor,
    }

    def __init__(
        self,
        schemas: list | None = None,
        error_handler: BaseErrorHandler = DefaultErrorHandler,
        renderer: BaseRenderer = DefaultRenderer,
    ) -> None:
        schemas = list(schemas) if isinstance(schemas, (list, tuple, set)) else []
        super().__init__(
            schemas=schemas, error_handler=error_handler, renderer=renderer
        )

    @classmethod
    def dynamic_descriptor(cls, passed_in_types: list) -> type:  # noqa: C901
        T = TypeVar("T", *passed_in_types)

        class DynamicDescriptor(bases.SpecialKeywordDescriptor[T]):
            def __init__(self, *, default=None, metadata=None) -> None:
                super().__init__(default=default, metadata=metadata or {})

            def __set__(self, obj, value):
                errors = (
                    obj.__dict__.get("_validation_errors")
                    if hasattr(obj, "__dict__")
                    else None
                )
                try:
                    if value is REQUIRED_MISSING:
                        raise e.RequiredPropertyViolation(
                            f"{self._name} is a required property"
                        )
                    types_to_check = getattr(T, "__constraints__", ())
                    if types_to_check:
                        if isinstance(value, bool) and bool not in types_to_check:
                            raise e.ValueTypeViolation("failed field constraints")
                        if not isinstance(value, types_to_check):
                            raise e.ValueTypeViolation(
                                f"failed field constraints: {types_to_check}"
                            )

                    for c in passed_in_types:
                        bases.SpecialKeywordDescriptor.process_child_descriptors(
                            self._name, c, value
                        )

                    with self.dynamic_child_descriptors(obj, value):
                        super().__set__(obj, value)
                except e.SchemaViolation as exc:
                    if errors is not None:
                        errors.append(exc)
                        if hasattr(obj, "__dict__"):
                            obj.__dict__[self._name] = value
                        else:
                            self.__dict__[self._name] = value
                        return
                    raise

                if hasattr(obj, "__dict__"):
                    obj.__dict__[self._name] = value
                else:
                    self.__dict__[self._name] = value

        return DynamicDescriptor

    def process_object(  # noqa: C901
        self, schema: dict, required_fields: list | None = None
    ) -> tuple:
        if required_fields is None:
            if "required" in schema:
                req = schema["required"]
                required_fields = (
                    list(req) if isinstance(req, (list, tuple, set)) else []
                )
            else:
                required_fields = list(schema.get("properties", {}).keys())
        else:
            required_fields = (
                list(required_fields)
                if isinstance(required_fields, (list, tuple, set))
                else []
            )

        fields = deque()
        fields_with_defaults = deque()

        for k in v2.process_keys(schema):
            v = schema.get("properties", {}).get(k, {})
            field_meta = {}

            if "anyOf" in v:
                subschemas = v.get("anyOf", [])
                inner_types = []
                if not v.get("type", None):
                    inner_types = [
                        DEFAULT_FACTORIES.get(subschema.get("type"))
                        for subschema in subschemas
                        if subschema.get("type", None)
                    ]
                else:
                    inner_types.append(DEFAULT_FACTORIES.get(v.get("type")))
                ttype = self.dynamic_descriptor(inner_types)
                for guard in (
                    "anyOf",
                    "maxLength",
                    "minLength",
                    "enum",
                    "minimum",
                    "maximum",
                    "exclusiveMinimum",
                    "exclusiveMaximum",
                    "multipleOf",
                    "not",
                    "allOf",
                    "oneOf",
                    "minItems",
                    "maxItems",
                    "uniqueItems",
                    "contains",
                    "minContains",
                    "maxContains",
                ):
                    if guard in v:
                        field_meta[guard] = v[guard]
            elif "allOf" in v:
                subschemas = v.get("allOf", [])
                type_name = v.get("type")
                if not type_name:
                    for sub in subschemas:
                        if "type" in sub:
                            type_name = sub["type"]
                            break
                ttype = self.MAP_TTYPE.get(type_name, bases.JSONSchemaFieldDescriptor)
                for guard in (
                    "allOf",
                    "maxLength",
                    "minLength",
                    "enum",
                    "minimum",
                    "maximum",
                    "exclusiveMinimum",
                    "exclusiveMaximum",
                    "multipleOf",
                    "not",
                    "anyOf",
                    "oneOf",
                    "minItems",
                    "maxItems",
                    "uniqueItems",
                    "contains",
                    "minContains",
                    "maxContains",
                ):
                    if guard in v:
                        field_meta[guard] = v[guard]
            elif "oneOf" in v:
                subschemas = v.get("oneOf", [])
                type_name = v.get("type")
                if not type_name:
                    for sub in subschemas:
                        if "type" in sub:
                            type_name = sub["type"]
                            break
                ttype = self.MAP_TTYPE.get(type_name, bases.JSONSchemaFieldDescriptor)
                for guard in (
                    "oneOf",
                    "maxLength",
                    "minLength",
                    "enum",
                    "minimum",
                    "maximum",
                    "exclusiveMinimum",
                    "exclusiveMaximum",
                    "multipleOf",
                    "not",
                    "anyOf",
                    "allOf",
                    "minItems",
                    "maxItems",
                    "uniqueItems",
                    "contains",
                    "minContains",
                    "maxContains",
                ):
                    if guard in v:
                        field_meta[guard] = v[guard]
            elif "not" in v:
                type_name = v.get("type")
                ttype = self.MAP_TTYPE.get(type_name, bases.JSONSchemaFieldDescriptor)
                for guard in (
                    "not",
                    "maxLength",
                    "minLength",
                    "enum",
                    "minimum",
                    "maximum",
                    "exclusiveMinimum",
                    "exclusiveMaximum",
                    "multipleOf",
                    "anyOf",
                    "allOf",
                    "oneOf",
                    "minItems",
                    "maxItems",
                    "uniqueItems",
                    "contains",
                    "minContains",
                    "maxContains",
                ):
                    if guard in v:
                        field_meta[guard] = v[guard]
            else:
                ttype = self.MAP_TTYPE.get(
                    v.get("type", "string"), bases.JSONSchemaFieldDescriptor
                )
                for guard in (
                    "maxLength",
                    "minLength",
                    "enum",
                    "minimum",
                    "maximum",
                    "exclusiveMinimum",
                    "exclusiveMaximum",
                    "multipleOf",
                    "format",
                    "not",
                    "anyOf",
                    "allOf",
                    "oneOf",
                    "minItems",
                    "maxItems",
                    "uniqueItems",
                    "contains",
                    "minContains",
                    "maxContains",
                ):
                    if guard in v:
                        field_meta[guard] = v[guard]

            if k in required_fields:
                if "default" in v:
                    desc_inst = ttype(default=v.get("default"), metadata=field_meta)
                else:
                    desc_inst = ttype(default=REQUIRED_MISSING, metadata=field_meta)
                desc_inst.__set_name__(None, k)
                fields_with_defaults.append((k, ttype, desc_inst))
            else:
                if "default" in v:
                    default_val = v.get("default")
                else:
                    default_factory = DEFAULT_FACTORIES.get(v.get("type"), str)
                    default_val = (
                        default_factory()
                        if callable(default_factory)
                        else default_factory
                    )
                desc_inst = ttype(default=default_val, metadata=field_meta)
                desc_inst.__set_name__(None, k)
                fields_with_defaults.append((k, ttype, desc_inst))

        return fields, fields_with_defaults

    def register(self, schema: dict) -> bool:
        if not utils.is_schema_toplevel_object(schema):
            raise e.MalformedSchemaViolation()

        if "required" in schema:
            req = schema["required"]
            if (
                not isinstance(req, list)
                or not all(isinstance(x, str) for x in req)
                or len(req) != len(set(req))
            ):
                raise e.MalformedSchemaViolation(
                    "required keyword must be an array of unique strings"
                )
            required_fields = schema.get("required", [])
        else:
            required_fields = list(schema.get("properties", {}).keys())

        klassname = utils.generate_classname(schema.get("title"))

        fields, fields_with_defaults = self.process_object(
            schema, required_fields=required_fields
        )

        dataclass_fields = []
        descriptors_to_attach = {}

        for item in fields:
            k, desc_cls, desc_inst = item
            dataclass_fields.append((k, desc_cls))
            descriptors_to_attach[k] = desc_inst

        for item in fields_with_defaults:
            k, desc_cls, desc_inst = item
            dataclass_fields.append((k, desc_cls, desc_inst))
            descriptors_to_attach[k] = desc_inst

        prop_keys = list(schema.get("properties", {}).keys())

        dklass = make_dataclass(
            klassname,
            dataclass_fields,
            frozen=True,
            namespace={
                "tocsv": lambda self, header=False, fields=prop_keys: (
                    f"{','.join(fields)}\n{','.join(str(getattr(self, i)) for i in fields)}"
                    if header
                    else ",".join(str(getattr(self, i)) for i in fields)
                ),
                "tolist": lambda self, fields=prop_keys: [
                    getattr(self, i) for i in fields
                ],
                "todict": lambda self, fields=prop_keys: {
                    i: getattr(self, i) for i in fields
                },
            },
        )

        for k, desc_inst in descriptors_to_attach.items():
            desc_inst.__set_name__(dklass, k)
            setattr(dklass, k, desc_inst)

        orig_init = dklass.__init__

        def wrapped_init(self, *args, **kwargs):
            self.__dict__["_validation_errors"] = []
            orig_init(self, *args, **kwargs)
            errors = self.__dict__.pop("_validation_errors", [])
            if not errors:
                return
            if len(errors) == 1:
                raise errors[0]
            raise ExceptionGroup("Validation errors", errors)

        dklass.__init__ = wrapped_init

        setattr(self.dmod, klassname, dklass)
        return True
