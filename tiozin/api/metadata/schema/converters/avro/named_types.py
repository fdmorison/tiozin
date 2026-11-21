"""
The named types of an Avro schema: records, enums and fixed types.

Avro defines a named type once and refers to it by name everywhere else. A
schema has no such references, so they are replaced by the definitions on the
way in, and put back on the way out.
"""

from __future__ import annotations

from typing import Any

from tiozin.utils import default

from ...exceptions import SchemaError
from . import constants as const


def full_name(named_type: dict[str, Any], namespace: str = None) -> str:
    """
    The name of a named type with its namespace, such as "com.acme.User".

    The namespace of the type wins over the given one, which is the namespace
    of the type around it. A name with a dot is already a full name.

    Examples:

        ```python
        full_name({"name": "User"})  # 'User'
        full_name({"name": "User"}, "com.acme")  # 'com.acme.User'
        full_name({"name": "User", "namespace": "com.geo"}, "com.acme")  # 'com.geo.User'
        full_name({"name": "geo.User"}, "com.acme")  # 'geo.User'
        ```
    """
    name = named_type["name"]
    namespace = named_type.get("namespace", namespace)

    return name if "." in name or not namespace else f"{namespace}.{name}"


def inline_named_types(
    avro_type: Any,
    namespace: str = None,
    named_types: dict[str, Any] = None,
) -> Any:
    """
    The Avro type with every reference to a named type replaced by its
    definition.

    The type is parsed JSON, as AvroType takes it. Use it on a whole record so
    that every named type is defined before it is referred to.

    Raises SchemaError when a name is unknown, or when a type refers to itself.

    Examples:

        ```python
        status = {"type": "enum", "name": "Status", "symbols": ["A"]}

        inline_named_types(
            {
                "type": "record",
                "name": "User",
                "fields": [
                    {"name": "status", "type": status},
                    {"name": "old_status", "type": "Status"},
                ],
            }
        )
        # {
        #     "type": "record",
        #     "name": "User",
        #     "fields": [
        #         {"name": "status", "type": status},
        #         {"name": "old_status", "type": status},
        #     ],
        # }
        ```
    """
    named_types = default(named_types, {})

    match avro_type:
        case str() as name if name in const.AVRO_KNOWN_TYPES:
            return name
        case str() as name:
            qualified_name = full_name({"name": name}, namespace)
            reference = qualified_name if qualified_name in named_types else name

            SchemaError.raise_if(
                reference not in named_types,
                f"Unsupported Avro type `{name}`",
            ).raise_if(
                named_types[reference] is None,
                f"Avro type `{name}` refers to itself, which a schema cannot represent",
            )

            return named_types[reference]
        case list() as union:
            return [inline_named_types(branch, namespace, named_types) for branch in union]
        case {"type": "record", "name": str(), "fields": list() as fields}:
            name = full_name(avro_type, namespace)
            record_namespace = name.rpartition(".")[0]
            named_types[name] = None

            record = {
                **avro_type,
                "fields": [
                    {
                        **field,
                        "type": inline_named_types(field["type"], record_namespace, named_types),
                    }
                    if isinstance(field, dict) and "type" in field
                    else field
                    for field in fields
                ],
            }
            named_types[name] = record

            return record
        case {"type": "enum" | "fixed", "name": str()}:
            named_types[full_name(avro_type, namespace)] = avro_type
            return avro_type
        case {"type": "array", "items": items}:
            return {**avro_type, "items": inline_named_types(items, namespace, named_types)}
        case {"type": "map", "values": values}:
            return {**avro_type, "values": inline_named_types(values, namespace, named_types)}
        case {"type": str() as name} if name not in const.AVRO_KNOWN_TYPES:
            return inline_named_types(name, namespace, named_types)
        case _:
            return avro_type


def reference_named_types(
    avro_type: Any,
    namespace: str = None,
    named_types: dict[str, Any] = None,
) -> Any:
    """
    The Avro type with every named type defined once, and referred to by name
    after that.

    This is the reverse of inline_named_types. The type is parsed JSON, as
    AvroType takes it.

    Raises SchemaError when two types have the same name and different
    definitions.

    Examples:

        ```python
        status = {"type": "enum", "name": "Status", "symbols": ["A"]}

        reference_named_types(
            {
                "type": "record",
                "name": "User",
                "fields": [
                    {"name": "status", "type": status},
                    {"name": "old_status", "type": status},
                ],
            }
        )
        # {
        #     "type": "record",
        #     "name": "User",
        #     "fields": [
        #         {"name": "status", "type": status},
        #         {"name": "old_status", "type": "Status"},
        #     ],
        # }
        ```
    """
    named_types = default(named_types, {})

    match avro_type:
        case list() as union:
            return [reference_named_types(branch, namespace, named_types) for branch in union]
        case {"type": str() as kind, "name": str()} if kind in const.AVRO_NAMED_TYPES:
            name = full_name(avro_type, namespace)
            type_namespace, _, simple_name = name.rpartition(".")

            if name in named_types:
                SchemaError.raise_if(
                    named_types[name] != avro_type,
                    f"Avro types named `{name}` have different definitions",
                )

                return simple_name if type_namespace == default(namespace, "") else name

            named_types[name] = avro_type

            match avro_type:
                case {"fields": list() as fields}:
                    return {
                        **avro_type,
                        "fields": [
                            {
                                **field,
                                "type": reference_named_types(
                                    field["type"],
                                    type_namespace,
                                    named_types,
                                ),
                            }
                            for field in fields
                        ],
                    }
                case _:
                    return avro_type
        case {"type": "array", "items": items}:
            return {**avro_type, "items": reference_named_types(items, namespace, named_types)}
        case {"type": "map", "values": values}:
            return {**avro_type, "values": reference_named_types(values, namespace, named_types)}
        case _:
            return avro_type
