from __future__ import annotations

import json
from typing import Any

from tiozin import config
from tiozin.utils import default

from ...exceptions import SchemaError
from ...model import EnumValue, LogicalType, Map, Property, Schema, StringFormat
from ...utils import without_none
from . import constants as const
from .avro_type import AvroType
from .named_types import reference_named_types


class AvroSchemaWriter:
    """
    Writes a schema as an Avro record schema in JSON.

    The Avro type comes from the logical type, the logical type options and
    the custom properties every converter shares, never from the physical
    type:

    - An integer is int or long, and a number is float or double, by its
      `format` option, long and double by default.
    - A number with `precision` and `scale` is a decimal, on a fixed type when
      it has a `typeSize`, otherwise on bytes.
    - A `binary` string is a fixed type when it has a `typeSize`, otherwise
      bytes.
    - A timestamp or a time takes its unit from `timeUnit`, micros by default,
      and a timestamp is local when its `timezone` option is false.
    - A string with the "uuid" format is a UUID, and a string with enum values
      is an Avro enum.

    A property that is not required becomes a union with null that defaults to
    null. Descriptions become `doc`.

    Some custom properties are written as Avro attributes: `default` and
    `order` on a field, and `typeName` and `namespace` on a record, enum or
    fixed type. Synonyms whose source is "avro" become aliases. Without a
    `typeName`, a nested type is named by its full path. A type that appears
    more than once is defined the first time and referred to by name after
    that.

    Every other custom property with only a name and a value is written as an
    Avro attribute of the same name: on the type when its vendor is "avro",
    otherwise on the field, or on the record for the schema. A name that Avro
    reserves, such as `type`, or that has a meaning elsewhere in Avro, such as
    `namespace` on a field, is not written this way.

    Every other attribute that Avro cannot express goes under `odcs`, on the
    record and on its fields, so nothing is lost when the result is read back.

    Raises SchemaError when a schema, property or type name, or an enum value,
    is not a valid Avro name, when a map key is not a string, when a property
    that is not a string has enum values, or when two types have the same name
    and different definitions.

    Examples:

        ```python
        schema = Schema(name="users").integer("id", required=True).string("email")

        AvroSchemaWriter().write(schema)
        # {
        #     "type": "record",
        #     "name": "users",
        #     "fields": [
        #         {"name": "id", "type": "long"},
        #         {"name": "email", "type": ["null", "string"], "default": None},
        #     ],
        # }
        ```
    """

    def write(self, schema: Schema) -> dict[str, Any]:
        """
        Writes a schema as an Avro record schema, as parsed JSON. A schema
        without a name becomes a record named "root".

        Raises SchemaError when the schema cannot be written as Avro.

        Examples:

            ```python
            AvroSchemaWriter().write(Schema(name="users").integer("id", required=True))
            # {"type": "record", "name": "users", "fields": [{"name": "id", "type": "long"}]}
            ```
        """
        name = default(schema.name, const.DEFAULT_RECORD_NAME)

        SchemaError.raise_if(
            not all(self.is_avro_name(part) for part in name.split(".")),
            f"Schema `{name}` is not a valid Avro name",
        )

        record = {
            **self.to_record(schema, name),
            **self.to_aliases(schema),
            **self.avro_attributes(schema, None, const.SCHEMA_RESERVED_KEYS),
        }

        if schema.description is not None:
            record["doc"] = schema.description

        declared = schema.model_dump(
            mode="json",
            by_alias=True,
            exclude_unset=True,
            exclude=const.SCHEMA_NATIVE_ATTRIBUTES,
        )
        odcs_attributes = {
            **self.unexpressed(declared, {"name": name}),
            **({"name": None} if schema.name is None else {}),
        }
        odcs_attributes = self.without_aliases(odcs_attributes)
        odcs_attributes = self.without_custom_properties(odcs_attributes, const.RECORD_PROPERTIES)
        odcs_attributes = self.without_avro_attributes(
            odcs_attributes, None, const.SCHEMA_RESERVED_KEYS
        )

        if odcs_attributes:
            record[const.ODCS_KEY] = odcs_attributes

        return reference_named_types(record)

    def to_record(self, element: Schema | Property, name: str) -> dict[str, Any]:
        """
        An Avro record of the given name, with one field per property of the
        schema or of the object property.

        Examples:

            ```python
            writer = AvroSchemaWriter()

            writer.to_record(Schema(name="users").integer("id", required=True), "users")
            # {"type": "record", "name": "users", "fields": [{"name": "id", "type": "long"}]}
            ```
        """
        record = self.to_named_type(element, "record", name)

        return {
            **record,
            "fields": [
                self.to_field(property, f"{name}.{property.name}")
                for property in element.properties or []
            ],
        }

    def to_field(self, property: Property, path: str) -> dict[str, Any]:
        """
        Converts a property to an Avro record field.

        In an optional field with a default value, null comes last in the
        union, because Avro requires the default to be of the first type.

        Raises SchemaError when the property name is not a valid Avro name.

        Examples:

            ```python
            writer = AvroSchemaWriter()

            writer.to_field(Property(name="id", logicalType="integer", required=True), "users.id")
            # {"name": "id", "type": "long"}

            writer.to_field(Property(name="email", logicalType="string"), "users.email")
            # {"name": "email", "type": ["null", "string"], "default": None}
            ```
        """
        SchemaError.raise_if(
            not self.is_avro_name(property.name),
            f"Property `{property.name}` is not a valid Avro name",
        )

        nullable_type = self.to_nullable_type(property, path)
        default_value = self.custom_value(property, const.DEFAULT_PROPERTY)

        if default_value is not None and not property.required:
            nullable_type = nullable_type[::-1]

        avro_type = AvroType(
            self.in_written_order(nullable_type, self.to_written_type(property.physicalType))
        )

        field = {
            "name": property.name,
            "type": avro_type.json_value,
            **self.to_aliases(property),
            **without_none({"order": self.custom_value(property, const.ORDER_PROPERTY)}),
            **self.avro_attributes(property, None, const.FIELD_RESERVED_KEYS),
        }

        if default_value is not None or not property.required:
            field["default"] = default_value

        if property.description is not None:
            field["doc"] = property.description

        odcs_attributes = self.odcs_attributes(property, avro_type)
        odcs_attributes = self.without_aliases(odcs_attributes)
        odcs_attributes = self.without_custom_properties(odcs_attributes, const.FIELD_PROPERTIES)
        odcs_attributes = self.without_avro_attributes(
            odcs_attributes, None, const.FIELD_RESERVED_KEYS
        )
        odcs_attributes.pop("description", None)

        if odcs_attributes:
            field[const.ODCS_KEY] = odcs_attributes

        return field

    def to_nullable_type(self, property: Property, path: str) -> Any:
        """
        The Avro type of a property, in a union with null when not required.

        Examples:

            ```python
            writer = AvroSchemaWriter()

            writer.to_nullable_type(Property(name="email", logicalType="string"), "users.email")
            # ["null", "string"]
            ```
        """
        avro_type = self.with_type_attributes(self.to_avro_type(property, path), property)
        return avro_type if property.required else [const.NULL_TYPE, avro_type]

    def with_type_attributes(self, avro_type: Any, property: Property) -> Any:
        """
        The Avro type with the custom properties of the property whose vendor
        is "avro" as attributes. What defines the type wins over them.

        Examples:

            ```python
            writer = AvroSchemaWriter()
            property = Property(
                name="name",
                customProperties=[
                    {"property": "avro.java.string", "value": "String", "vendor": "avro"}
                ],
            )

            writer.with_type_attributes("string", property)
            # {"type": "string", "avro.java.string": "String"}
            ```
        """
        type_attributes = self.avro_attributes(property, const.AVRO_VENDOR, const.TYPE_KEYS)

        match avro_type:
            case _ if not type_attributes:
                return avro_type
            case str() as type_name:
                return {"type": type_name, **type_attributes}
            case dict() as definition:
                return {**type_attributes, **definition}

    def to_avro_type(self, property: Property, path: str) -> Any:
        """
        The Avro type of a property. The path names a record, enum or fixed
        type that has no `typeName`.

        Raises SchemaError when the property has no type Avro can represent.

        Examples:

            ```python
            writer = AvroSchemaWriter()

            created_at = Property(name="created_at", logicalType="timestamp")
            writer.to_avro_type(created_at, "users.created_at")
            # {"type": "long", "logicalType": "timestamp-micros"}

            price = Property(
                name="price",
                logicalType="number",
                customProperties=[
                    {"property": "precision", "value": 10},
                    {"property": "scale", "value": 2},
                ],
            )
            writer.to_avro_type(price, "users.price")
            # {"type": "bytes", "logicalType": "decimal", "precision": 10, "scale": 2}
            ```
        """
        match property:
            case Property(enum=list()) if property.logicalType != LogicalType.STRING:
                raise SchemaError(
                    f"Property `{property.name}` has enum values, but Avro enums only hold strings"
                )
            case Property(items=Property() as items):
                return {
                    "type": "array",
                    "items": self.to_nullable_type(items, f"{path}.items"),
                }
            case Property(map=Map(key=key)) if key is not None and (
                key.logicalType not in const.MAP_KEY_LOGICAL_TYPES
            ):
                raise SchemaError(f"Map property `{property.name}` needs a string key for Avro")
            case Property(map=Map(value=Property() as value)):
                return {
                    "type": "map",
                    "values": self.to_nullable_type(value, f"{path}.values"),
                }
            case Property(map=Map()):
                raise SchemaError(f"Map property `{property.name}` needs a value definition")
            case Property(properties=list()) | Property(logicalType=LogicalType.OBJECT):
                return self.to_record(property, self.to_type_name(property, path))
            case Property(logicalType=LogicalType.STRING, enum=list() as values):
                return self.to_enum(property, values, path)
            case Property(logicalType=LogicalType.NUMBER, precision=int()):
                return self.to_decimal_type(property, path)
            case Property(logicalType=LogicalType.STRING, binary=True):
                return self.to_binary_type(property, path)
            case Property(logicalType=LogicalType.TIMESTAMP | LogicalType.TIME):
                return self.to_primitive_type(self.to_temporal_type_name(property))
            case Property(logicalType=LogicalType.STRING) if (
                self.option_value(property, "format") == StringFormat.UUID
            ):
                return self.to_primitive_type(const.UUID_LOGICAL_TYPE)
            case Property(logicalType=LogicalType.INTEGER):
                return self.to_sized_type(
                    property, const.AVRO_INTEGER_BY_FORMAT, config.default_schema_integer_format
                )
            case Property(logicalType=LogicalType.NUMBER):
                return self.to_sized_type(
                    property, const.AVRO_NUMBER_BY_FORMAT, config.default_schema_number_format
                )
            case Property(logicalType=logical_type) if logical_type in const.LOGICAL_TO_AVRO:
                return self.to_primitive_type(const.LOGICAL_TO_AVRO[logical_type])
            case _:
                raise SchemaError(f"Property `{property.name}` has no type Avro can represent")

    def to_type_name(self, property: Property, path: str) -> str:
        """
        The name of the record, enum or fixed type of a property: its
        `typeName` custom property, or its path.

        Examples:

            ```python
            writer = AvroSchemaWriter()

            writer.to_type_name(Property(name="address", logicalType="object"), "users.address")
            # 'users.address'

            address = Property(
                name="address",
                logicalType="object",
                customProperties=[{"property": "typeName", "value": "Address"}],
            )
            writer.to_type_name(address, "users.address")
            # 'Address'
            ```
        """
        return default(property.typeName, path)

    def to_named_type(
        self, element: Schema | Property, type_name: str, name: str
    ) -> dict[str, Any]:
        """
        The start of an Avro record, enum or fixed type: its type, its name and
        its namespace.

        Raises SchemaError when the name is not a valid Avro name.

        Examples:

            ```python
            writer = AvroSchemaWriter()
            address = Property(
                name="address",
                customProperties=[{"property": "namespace", "value": "com.acme"}],
            )

            writer.to_named_type(address, "record", "Address")
            # {"type": "record", "name": "Address", "namespace": "com.acme"}
            ```
        """
        SchemaError.raise_if(
            not isinstance(name, str)
            or not all(self.is_avro_name(part) for part in name.split(".")),
            f"Type `{name}` is not a valid Avro name",
        )

        return without_none(
            {
                "type": type_name,
                "name": name,
                "namespace": element.namespace,
            }
        )

    def to_enum(self, property: Property, values: list[EnumValue], path: str) -> dict[str, Any]:
        """
        An Avro enum with one symbol per enum value.

        Raises SchemaError when an enum value is not a valid Avro name.

        Examples:

            ```python
            writer = AvroSchemaWriter()
            status = Property(
                name="status",
                logicalType="string",
                enum=[{"value": "ACTIVE"}, {"value": "BLOCKED"}],
            )

            writer.to_enum(status, status.enum, "users.status")
            # {"type": "enum", "name": "users.status", "symbols": ["ACTIVE", "BLOCKED"]}
            ```
        """
        symbols = [enum_value.value for enum_value in values]

        SchemaError.raise_if(
            not all(isinstance(symbol, str) and self.is_avro_name(symbol) for symbol in symbols),
            f"Enum values of `{property.name}` are not valid Avro names",
        )

        return {
            **self.to_named_type(property, "enum", self.to_type_name(property, path)),
            "symbols": symbols,
        }

    def to_decimal_type(self, property: Property, path: str) -> dict[str, Any]:
        """
        The Avro decimal type for a number with a `precision` custom property,
        on a fixed type when it has a `typeSize`, otherwise on bytes.
        """
        primitive = (
            self.to_fixed_type(property, path)
            if property.typeSize is not None
            else {"type": const.AVRO_LOGICAL_TO_PRIMITIVE[const.DECIMAL_LOGICAL_TYPE]}
        )

        return {
            **primitive,
            "logicalType": const.DECIMAL_LOGICAL_TYPE,
            **without_none(
                {
                    "precision": property.precision,
                    "scale": property.scale,
                }
            ),
        }

    def to_binary_type(self, property: Property, path: str) -> str | dict[str, Any]:
        """
        The Avro type of a binary string: a fixed type when it has a
        `typeSize`, otherwise bytes.
        """
        if property.typeSize is None:
            return const.BYTES_TYPE

        return self.to_fixed_type(property, path)

    def to_sized_type(
        self,
        property: Property,
        types_by_format: dict[str, str],
        default_format: str,
    ) -> str:
        """
        The Avro type for the size of an integer or a number, given by the
        `format` option, or the default format when it has none.

        Raises SchemaError when Avro has no type of that size.
        """
        size_format = default(self.option_value(property, "format"), default_format)

        SchemaError.raise_if(
            size_format not in types_by_format,
            f"Property `{property.name}` has no Avro type for format `{size_format}`",
        )

        return types_by_format[size_format]

    def to_fixed_type(self, property: Property, path: str) -> dict[str, Any]:
        """
        The Avro fixed type of a property, with the size of its `typeSize`.
        """
        return {
            **self.to_named_type(property, const.FIXED_TYPE, self.to_type_name(property, path)),
            "size": property.typeSize,
        }

    def to_temporal_type_name(self, property: Property) -> str:
        """
        The Avro logical type of a timestamp or a time, from its `timeUnit`
        custom property, micros by default, and, for a timestamp, from whether
        it carries its timezone, which it does by default.

        Raises SchemaError when Avro has no type for that unit.
        """
        time_unit = default(property.timeUnit, config.default_schema_time_unit)
        timezone = (
            self.option_value(property, "timezone") is not False
            if property.logicalType == LogicalType.TIMESTAMP
            else None
        )
        temporal = (property.logicalType, timezone, time_unit)
        type_name = next(
            (
                name
                for name, avro_temporal in const.AVRO_TEMPORAL_TYPES.items()
                if avro_temporal == temporal
            ),
            None,
        )

        SchemaError.raise_if(
            type_name is None,
            f"Property `{property.name}` has no Avro type for a {property.logicalType} "
            f"in {time_unit}",
        )

        return type_name

    def odcs_attributes(
        self,
        property: Property,
        avro_type: AvroType,
        tracks_nullability: bool = None,
    ) -> dict[str, Any]:
        """
        The attributes of the property that the Avro type cannot express.

        Pass `tracks_nullability=False` for map keys. Avro has no null for
        them, so `required` is kept as declared.

        Examples:

            ```python
            writer = AvroSchemaWriter()
            email = Property(name="email", logicalType="string", classification="pii")

            writer.odcs_attributes(email, AvroType(["null", "string"]))
            # {"classification": "pii"}
            ```
        """
        tracks_nullability = default(tracks_nullability, True)
        value_type = avro_type.non_null

        declared = property.model_dump(
            mode="json",
            by_alias=True,
            exclude_unset=True,
            exclude=const.PROPERTY_NATIVE_ATTRIBUTES,
        )
        implied = dict(value_type.attributes)

        if tracks_nullability and not avro_type.is_nullable:
            implied["required"] = True

        odcs_attributes = self.unexpressed(declared, implied)
        odcs_attributes = self.without_implied_custom_properties(
            odcs_attributes,
            [*value_type.type_parameters, *value_type.custom_properties],
        )

        match property:
            case Property(items=Property() as items):
                nested_attributes = {
                    "items": self.odcs_attributes(items, value_type.items),
                }
            case Property(map=Map(key=key, value=Property() as value)):
                map_attributes = {
                    "key": None
                    if key is None
                    else self.odcs_attributes(
                        key,
                        AvroType(const.MAP_KEY_TYPE),
                        tracks_nullability=False,
                    ),
                    "value": self.odcs_attributes(value, value_type.values),
                }
                nested_attributes = {
                    "map": {
                        entry: value
                        for entry, value in map_attributes.items()
                        if value is None or value
                    },
                }
            case _:
                nested_attributes = {}

        nested_attributes = {key: value for key, value in nested_attributes.items() if value}

        return {**odcs_attributes, **nested_attributes}

    @staticmethod
    def unexpressed(declared: dict[str, Any], implied: dict[str, Any]) -> dict[str, Any]:
        """
        The declared attributes that differ from the ones Avro implies.

        Examples:

            ```python
            AvroSchemaWriter.unexpressed(
                {"logicalType": "integer", "required": True, "classification": "pii"},
                {"logicalType": "integer", "required": True},
            )
            # {"classification": "pii"}
            ```
        """
        return {key: value for key, value in declared.items() if value != implied.get(key)}

    @staticmethod
    def without_custom_properties(attributes: dict[str, Any], names: set[str]) -> dict[str, Any]:
        """
        The attributes without the custom properties of the given names, which
        are written as Avro attributes.

        Examples:

            ```python
            AvroSchemaWriter.without_custom_properties(
                {
                    "customProperties": [
                        {"property": "default", "value": 0},
                        {"property": "owner", "value": "sales"},
                    ]
                },
                {"default"},
            )
            # {"customProperties": [{"property": "owner", "value": "sales"}]}
            ```
        """
        custom_properties = [
            custom_property
            for custom_property in attributes.get("customProperties", [])
            if custom_property["property"] not in names
        ]
        others = {key: value for key, value in attributes.items() if key != "customProperties"}

        return {**others, "customProperties": custom_properties} if custom_properties else others

    @classmethod
    def avro_attributes(
        cls,
        element: Schema | Property,
        vendor: str | None,
        reserved: set[str],
    ) -> dict[str, Any]:
        """
        The custom properties of the given vendor that are written as Avro
        attributes, by name. Pass None as the vendor for those without one.

        Examples:

            ```python
            property = Property(
                name="name",
                customProperties=[
                    {"property": "avro.java.string", "value": "String", "vendor": "avro"}
                ],
            )

            AvroSchemaWriter.avro_attributes(property, "avro", {"type"})
            # {"avro.java.string": "String"}
            ```
        """
        custom_properties = [
            custom_property.model_dump(mode="json", exclude_unset=True)
            for custom_property in element.customProperties or []
        ]

        return {
            custom_property["property"]: custom_property.get("value")
            for custom_property in custom_properties
            if cls.is_avro_attribute(custom_property, vendor, reserved)
        }

    @classmethod
    def without_avro_attributes(
        cls,
        attributes: dict[str, Any],
        vendor: str | None,
        reserved: set[str],
    ) -> dict[str, Any]:
        """
        The attributes without the custom properties of the given vendor that
        are written as Avro attributes.

        Examples:

            ```python
            AvroSchemaWriter.without_avro_attributes(
                {
                    "customProperties": [
                        {"property": "avro.java.string", "value": "String", "vendor": "avro"},
                        {"property": "owner", "value": "sales"},
                    ]
                },
                "avro",
                {"type"},
            )
            # {"customProperties": [{"property": "owner", "value": "sales"}]}
            ```
        """
        custom_properties = [
            custom_property
            for custom_property in attributes.get("customProperties", [])
            if not cls.is_avro_attribute(custom_property, vendor, reserved)
        ]
        others = {key: value for key, value in attributes.items() if key != "customProperties"}

        return {**others, "customProperties": custom_properties} if custom_properties else others

    @staticmethod
    def is_avro_attribute(
        custom_property: dict[str, Any],
        vendor: str | None,
        reserved: set[str],
    ) -> bool:
        """
        Whether the custom property is written as an Avro attribute: it has
        the given vendor, only a name and a value besides, and a name that Avro
        does not reserve.

        Examples:

            ```python
            custom_property = {"property": "avro.java.string", "value": "String", "vendor": "avro"}

            AvroSchemaWriter.is_avro_attribute(custom_property, "avro", {"type"})  # True
            AvroSchemaWriter.is_avro_attribute(custom_property, None, {"type"})  # False
            ```
        """
        return (
            custom_property.get("vendor") == vendor
            and custom_property.get("id") is None
            and custom_property.get("description") is None
            and custom_property["property"] not in reserved
        )

    @staticmethod
    def without_aliases(attributes: dict[str, Any]) -> dict[str, Any]:
        """
        The attributes without the synonyms whose source is "avro", which are
        written as Avro aliases.

        Examples:

            ```python
            AvroSchemaWriter.without_aliases(
                {"synonyms": [{"synonym": "user_id", "source": "avro"}, {"synonym": "uid"}]}
            )
            # {"synonyms": [{"synonym": "uid"}]}
            ```
        """
        synonyms = [
            synonym
            for synonym in attributes.get("synonyms", [])
            if synonym.get("source") != const.ALIAS_SOURCE
        ]
        others = {key: value for key, value in attributes.items() if key != "synonyms"}

        return {**others, "synonyms": synonyms} if synonyms else others

    @staticmethod
    def without_implied_custom_properties(
        attributes: dict[str, Any],
        implied: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        The attributes without the custom properties the Avro type already
        holds, such as its `precision` or its name.
        """
        custom_properties = [
            custom_property
            for custom_property in attributes.get("customProperties", [])
            if custom_property not in implied
        ]
        others = {key: value for key, value in attributes.items() if key != "customProperties"}

        return {**others, "customProperties": custom_properties} if custom_properties else others

    @classmethod
    def in_written_order(cls, generated: Any, written: Any) -> Any:
        """
        The generated type with the keys of each definition in the order the
        written type has them, so a type read from Avro is written back as it
        was. Only the order changes: the values are always the generated ones.

        Examples:

            ```python
            AvroSchemaWriter.in_written_order(
                {"type": "fixed", "name": "Hash", "size": 16},
                {"size": 16, "type": "fixed", "name": "Hash"},
            )
            # {"size": 16, "type": "fixed", "name": "Hash"}
            ```
        """
        match generated, written:
            case dict(), dict():
                keys = [key for key in written if key in generated] + [
                    key for key in generated if key not in written
                ]
                return {key: cls.in_written_order(generated[key], written.get(key)) for key in keys}
            case list(), list() if len(generated) == len(written):
                return [
                    cls.in_written_order(generated_item, written_item)
                    for generated_item, written_item in zip(generated, written, strict=True)
                ]
            case _:
                return generated

    @staticmethod
    def to_written_type(physical_type: str | None) -> Any:
        """
        The Avro type a physical type writes: its JSON when it is JSON,
        otherwise the name as is.
        """
        try:
            return json.loads(physical_type)
        except (TypeError, ValueError):
            return physical_type

    @staticmethod
    def option_value(property: Property, name: str) -> Any:
        """
        The value of the logical type option with the given name, or None when
        the option is not set.
        """
        options = property.logicalTypeOptions

        if options is None or name not in options.model_fields_set:
            return None

        return getattr(options, name)

    @staticmethod
    def custom_value(element: Schema | Property, name: str) -> Any:
        """
        The value of the custom property with the given name and no vendor,
        or None.

        Examples:

            ```python
            property = Property(
                name="score",
                customProperties=[{"property": "default", "value": 0}],
            )

            AvroSchemaWriter.custom_value(property, "default")  # 0
            AvroSchemaWriter.custom_value(property, "order")  # None
            ```
        """
        return next(
            (
                custom_property.value
                for custom_property in element.customProperties or []
                if custom_property.property == name and custom_property.vendor is None
            ),
            None,
        )

    @staticmethod
    def to_aliases(element: Schema | Property) -> dict[str, Any]:
        """
        The synonyms whose source is "avro", as Avro aliases.

        Examples:

            ```python
            property = Property(
                name="id",
                synonyms=[{"synonym": "user_id", "source": "avro"}, {"synonym": "uid"}],
            )

            AvroSchemaWriter.to_aliases(property)  # {"aliases": ["user_id"]}
            ```
        """
        aliases = [
            synonym.synonym
            for synonym in element.synonyms or []
            if synonym.source == const.ALIAS_SOURCE
        ]

        return {"aliases": aliases} if aliases else {}

    @staticmethod
    def is_avro_name(name: str | None) -> bool:
        """
        Whether the name is a valid Avro name, without dots.

        Examples:

            ```python
            AvroSchemaWriter.is_avro_name("user_id")  # True
            AvroSchemaWriter.is_avro_name("user-id")  # False
            AvroSchemaWriter.is_avro_name("com.acme")  # False
            ```
        """
        return name is not None and const.AVRO_NAME_PATTERN.fullmatch(name) is not None

    @staticmethod
    def to_primitive_type(type_name: str) -> str | dict[str, str]:
        """
        An Avro primitive type, or a logical type on its primitive, by name.

        Examples:

            ```python
            AvroSchemaWriter.to_primitive_type("long")  # 'long'
            AvroSchemaWriter.to_primitive_type("timestamp-micros")
            # {"type": "long", "logicalType": "timestamp-micros"}
            ```
        """
        primitive = const.AVRO_LOGICAL_TO_PRIMITIVE.get(type_name)
        return type_name if primitive is None else {"type": primitive, "logicalType": type_name}
