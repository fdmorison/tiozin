from __future__ import annotations

import json
from typing import Any

from ...exceptions import SchemaError
from ...model import LogicalType, StringFormat, TiozinCustomProperty
from ...utils import without_none
from . import constants as const


class AvroType:
    """
    An Avro type, given as parsed JSON.

    The value is what `json.loads` returns for the type: a str with the name of
    a primitive type, a dict for a complex or logical type, or a list for a
    union with null. JSON text is not accepted: a str is always read as a type
    name, so a string holding a whole JSON document is an unsupported type.

    Examples:

        A primitive type, by name:

        ```python
        AvroType("long")
        AvroType("string")
        ```

        A union with null, for a type that can be missing:

        ```python
        AvroType(["null", "string"])
        ```

        A logical type on its primitive:

        ```python
        AvroType({"type": "long", "logicalType": "timestamp-micros"})
        AvroType({"type": "bytes", "logicalType": "decimal", "precision": 10, "scale": 2})
        ```

        Complex types:

        ```python
        AvroType({"type": "record", "name": "users", "fields": [{"name": "id", "type": "long"}]})
        AvroType({"type": "array", "items": "string"})
        AvroType({"type": "map", "values": "long"})
        AvroType({"type": "enum", "name": "status", "symbols": ["ACTIVE", "BLOCKED"]})
        AvroType({"type": "fixed", "name": "hash", "size": 16})
        ```

        Parse JSON text before passing it:

        ```python
        AvroType(json.loads('{"type": "array", "items": "string"}'))
        ```
    """

    def __init__(self, json_value: str | dict[str, Any] | list[Any]) -> None:
        self.json_value = json_value

    @property
    def is_nullable(self) -> bool:
        """
        Whether the type is a union with null.

        Examples:

            ```python
            AvroType(["null", "long"]).is_nullable  # True
            AvroType(["long"]).is_nullable  # False
            AvroType("long").is_nullable  # False
            ```
        """
        return isinstance(self.json_value, list) and const.NULL_TYPE in self.json_value

    @property
    def non_null(self) -> AvroType:
        """
        The type without its null branch. A union of a single type gives that
        type, and a type that is not a union is returned as is.

        Raises SchemaError when a union has more than one type besides null.

        Examples:

            ```python
            AvroType(["null", "long"]).non_null.json_value  # 'long'
            AvroType("long").non_null.json_value  # 'long'
            AvroType(["null", "long", "string"]).non_null  # raises SchemaError
            ```
        """
        match self.json_value:
            case [const.NULL_TYPE, other] | [other, const.NULL_TYPE] if other != const.NULL_TYPE:
                return AvroType(other)
            case [other] if other != const.NULL_TYPE:
                return AvroType(other)
            case list():
                raise SchemaError(f"Unsupported Avro union `{self.json_value}`")
            case _:
                return self

    @property
    def type_name(self) -> str:
        """
        The name of the type: the logical type when there is one, otherwise
        the primitive or complex type.

        Raises SchemaError when the type is not supported.

        Examples:

            ```python
            AvroType("long").type_name  # 'long'
            AvroType({"type": "array", "items": "string"}).type_name  # 'array'

            timestamp = AvroType({"type": "long", "logicalType": "timestamp-millis"})
            timestamp.type_name  # 'timestamp-millis'

            decimal = AvroType({"type": "bytes", "logicalType": "decimal", "precision": 10})
            decimal.type_name  # 'decimal'
            ```
        """
        match self.json_value:
            case {"logicalType": const.DECIMAL_LOGICAL_TYPE}:
                return const.DECIMAL_LOGICAL_TYPE
            case {"type": str() as name} if name in const.AVRO_COMPLEX_TO_LOGICAL:
                return name
            case {"logicalType": str() as name} if name in const.AVRO_TO_LOGICAL:
                return name
            case {"type": str() as name} | (str() as name) if name in const.AVRO_TO_LOGICAL:
                return name
            case _:
                raise SchemaError(f"Unsupported Avro type `{self.json_value}`")

    @property
    def logical_type(self) -> LogicalType:
        """
        The logical type of a property of this type.

        Examples:

            ```python
            AvroType("int").logical_type  # LogicalType.INTEGER
            AvroType({"type": "int", "logicalType": "date"}).logical_type  # LogicalType.DATE

            status = AvroType({"type": "enum", "name": "status", "symbols": ["A"]})
            status.logical_type  # LogicalType.STRING

            users = AvroType({"type": "record", "name": "users", "fields": []})
            users.logical_type  # LogicalType.OBJECT
            ```
        """
        match self.type_name:
            case const.DECIMAL_LOGICAL_TYPE:
                return LogicalType.NUMBER
            case name if name in const.AVRO_COMPLEX_TO_LOGICAL:
                return const.AVRO_COMPLEX_TO_LOGICAL[name]
            case name:
                return const.AVRO_TO_LOGICAL[name]

    @property
    def physical_type(self) -> str:
        """
        The type exactly as the Avro schema writes it: a name as is, and any
        other type, unions included, as its JSON.

        Examples:

            ```python
            AvroType("long").physical_type  # 'long'
            AvroType(["null", "string"]).physical_type  # '["null", "string"]'
            AvroType({"type": "int", "logicalType": "date"}).physical_type
            # '{"type": "int", "logicalType": "date"}'
            ```
        """
        match self.json_value:
            case str() as name:
                return name
            case written:
                return json.dumps(written)

    @property
    def type_parameters(self) -> list[dict[str, Any]]:
        """
        The parameters of the type, as the custom properties every converter
        shares: `binary` of bytes and fixed types, `precision` and `scale` of a
        decimal, `typeSize` of a fixed type, and `timeUnit` of a timestamp or a
        time.

        Raises SchemaError when a decimal has no precision, or a fixed type has
        no size.

        Examples:

            ```python
            AvroType(
                {"type": "bytes", "logicalType": "decimal", "precision": 10, "scale": 2}
            ).type_parameters
            # [{"property": "precision", "value": 10}, {"property": "scale", "value": 2}]

            AvroType({"type": "fixed", "name": "hash", "size": 16}).type_parameters
            # [{"property": "binary", "value": True}, {"property": "typeSize", "value": 16}]

            AvroType("bytes").type_parameters
            # [{"property": "binary", "value": True}]

            AvroType({"type": "long", "logicalType": "timestamp-millis"}).type_parameters
            # [{"property": "timeUnit", "value": "millis"}]
            ```
        """
        is_fixed = (
            isinstance(self.json_value, dict) and self.json_value.get("type") == const.FIXED_TYPE
        )

        SchemaError.raise_if(
            is_fixed and not isinstance(self.json_value.get("size"), int),
            f"Avro fixed `{self.json_value}` has no size",
        )

        match self.type_name:
            case const.DECIMAL_LOGICAL_TYPE:
                SchemaError.raise_if(
                    not isinstance(self.json_value.get("precision"), int),
                    f"Avro decimal `{self.json_value}` has no precision",
                )
                parameters = {
                    TiozinCustomProperty.PRECISION: self.json_value["precision"],
                    TiozinCustomProperty.SCALE: self.json_value.get("scale"),
                    TiozinCustomProperty.TYPE_SIZE: self.json_value.get("size")
                    if is_fixed
                    else None,
                }
            case const.FIXED_TYPE:
                parameters = {
                    TiozinCustomProperty.BINARY: True,
                    TiozinCustomProperty.TYPE_SIZE: self.json_value["size"],
                }
            case const.BYTES_TYPE:
                parameters = {TiozinCustomProperty.BINARY: True}
            case name if name in const.AVRO_TEMPORAL_TYPES:
                _, _, time_unit = const.AVRO_TEMPORAL_TYPES[name]
                parameters = {TiozinCustomProperty.TIME_UNIT: time_unit}
            case _:
                parameters = {}

        return [
            {"property": key, "value": value} for key, value in without_none(parameters).items()
        ]

    @property
    def logical_type_options(self) -> dict[str, Any] | None:
        """
        The logical type options the type implies: the size of an integer or a
        number, whether a timestamp carries its timezone, and the "uuid" format
        of a UUID. None for other types.

        Examples:

            ```python
            AvroType({"type": "long", "logicalType": "timestamp-micros"}).logical_type_options
            # {"timezone": True}

            AvroType({"type": "long", "logicalType": "local-timestamp-micros"}).logical_type_options
            # {"timezone": False}

            AvroType({"type": "string", "logicalType": "uuid"}).logical_type_options
            # {"format": "uuid"}

            AvroType("int").logical_type_options  # {"format": "i32"}
            ```
        """
        match self.type_name:
            case name if name in const.AVRO_TEMPORAL_TYPES:
                _, timezone, _ = const.AVRO_TEMPORAL_TYPES[name]
                return without_none({"timezone": timezone}) or None
            case const.UUID_LOGICAL_TYPE:
                return {"format": StringFormat.UUID}
            case name if name in const.AVRO_FORMATS:
                return {"format": const.AVRO_FORMATS[name]}
            case _:
                return None

    @property
    def custom_properties(self) -> list[dict[str, Any]]:
        """
        What the type holds besides its definition, as custom properties.

        The name and the namespace of a record, enum or fixed type keep their
        names. Every other attribute of the type, such as "avro.java.string"
        or a logical type this package does not know, keeps its name and has
        "avro" as its vendor.

        Examples:

            ```python
            AvroType(
                {"type": "record", "name": "Address", "namespace": "com.acme.geo", "fields": []}
            ).custom_properties
            # [
            #     {"property": "typeName", "value": "Address"},
            #     {"property": "namespace", "value": "com.acme.geo"},
            # ]

            AvroType({"type": "string", "avro.java.string": "String"}).custom_properties
            # [{"property": "avro.java.string", "value": "String", "vendor": "avro"}]

            AvroType({"type": "array", "items": "string"}).custom_properties  # []
            ```
        """
        match self.json_value:
            case {"type": str() as kind, "name": str() as name} if kind in const.AVRO_NAMED_TYPES:
                named = {
                    TiozinCustomProperty.TYPE_NAME: name,
                    TiozinCustomProperty.NAMESPACE: self.json_value.get("namespace"),
                }
                named_properties = [
                    {"property": key, "value": value} for key, value in without_none(named).items()
                ]
            case _:
                named_properties = []

        type_properties = [
            {"property": key, "value": value, "vendor": const.AVRO_VENDOR}
            for key, value in self.extra_attributes.items()
        ]

        return [*named_properties, *type_properties]

    @property
    def extra_attributes(self) -> dict[str, Any]:
        """
        The attributes of the type that Avro does not use to define it. A
        logical type this package does not know is one of them.

        Examples:

            ```python
            AvroType({"type": "string", "avro.java.string": "String"}).extra_attributes
            # {"avro.java.string": "String"}

            AvroType("string").extra_attributes  # {}
            ```
        """
        match self.json_value:
            case dict() as definition:
                return {
                    key: value
                    for key, value in definition.items()
                    if key not in const.TYPE_KEYS
                    and not (
                        key == const.LOGICAL_TYPE_KEY and value in const.UNDERSTOOD_LOGICAL_TYPES
                    )
                }
            case _:
                return {}

    @property
    def enum_values(self) -> list[dict[str, Any]] | None:
        """
        The symbols of an enum as enum values. None for every other type.

        Raises SchemaError when an enum has no symbols.

        Examples:

            ```python
            AvroType({"type": "enum", "name": "status", "symbols": ["A", "B"]}).enum_values
            # [{"value": "A"}, {"value": "B"}]

            AvroType("string").enum_values  # None
            ```
        """
        match self.json_value:
            case {"type": "enum", "symbols": list() as symbols}:
                return [{"value": symbol} for symbol in symbols]
            case {"type": "enum"}:
                raise SchemaError(f"Unsupported Avro type `{self.json_value}`")
            case _:
                return None

    @property
    def attributes(self) -> dict[str, Any]:
        """
        The property attributes the type implies: its logical type, and its
        physical type, logical type options and enum values when it has them.

        Examples:

            ```python
            AvroType("long").attributes
            # {"logicalType": "integer", "physicalType": "long"}

            AvroType({"type": "enum", "name": "status", "symbols": ["A"]}).attributes
            # {"logicalType": "string", "physicalType": "enum", "enum": [{"value": "A"}]}
            ```
        """
        return without_none(
            {
                "logicalType": self.logical_type,
                "physicalType": self.physical_type,
                "logicalTypeOptions": self.logical_type_options,
                "enum": self.enum_values,
            }
        )

    @property
    def fields(self) -> list[dict[str, Any]]:
        """
        The fields of a record, as parsed JSON.

        Raises SchemaError when the record has no fields.

        Examples:

            ```python
            AvroType(
                {"type": "record", "name": "users", "fields": [{"name": "id", "type": "long"}]}
            ).fields
            # [{"name": "id", "type": "long"}]
            ```
        """
        SchemaError.raise_if(
            "fields" not in self.json_value,
            f"Avro record `{self.json_value.get('name')}` has no fields",
        )

        return self.json_value["fields"]

    @property
    def items(self) -> AvroType:
        """
        The type of the items of an array.

        Raises SchemaError when the array has no items.

        Examples:

            ```python
            AvroType({"type": "array", "items": ["null", "string"]}).items.json_value
            # ['null', 'string']
            ```
        """
        SchemaError.raise_if(
            "items" not in self.json_value,
            f"Unsupported Avro type `{self.json_value}`",
        )

        return AvroType(self.json_value["items"])

    @property
    def values(self) -> AvroType:
        """
        The type of the values of a map.

        Raises SchemaError when the map has no values.

        Examples:

            ```python
            AvroType({"type": "map", "values": "long"}).values.json_value  # 'long'
            ```
        """
        SchemaError.raise_if(
            "values" not in self.json_value,
            f"Unsupported Avro type `{self.json_value}`",
        )

        return AvroType(self.json_value["values"])
