from __future__ import annotations

from typing import Any

from ...exceptions import SchemaError
from ...model import Property, Schema, TiozinCustomProperty
from ...utils import without_none
from . import constants as const
from .avro_type import AvroType
from .named_types import inline_named_types


class AvroSchemaReader:
    """
    Reads a schema from an Avro record schema in JSON.

    The record name becomes the schema name and every `doc` becomes a
    description. A field is required unless its type is a union with null.

    The physical type is what Avro stores: a primitive type, "fixed" or
    "enum". Enums become strings that keep their symbols as enum values, and
    fixed types become strings. Decimals become numbers. The parameters of a
    type become the custom properties every converter shares: `precision` and
    `scale` of a decimal, `typeSize` of a fixed type, and `timeUnit` of a
    timestamp or a time. Whether a timestamp carries its timezone, and the
    "uuid" format of a UUID, go to the logical type options. The key of
    a map is a required string. A reference to a named type is read as the
    type it refers to.

    What a schema has no attribute for becomes custom properties: the
    `default` and the `order` of a field, and the `typeName` and the
    `namespace` of a record, enum or fixed type. Aliases become synonyms whose
    source is "avro".

    Every other attribute keeps its name as a custom property. Those of the
    record and of its fields have no vendor. Those of a type, such as
    "avro.java.string", have "avro" as their vendor.

    The attributes found under `odcs`, on the record and on its fields, set
    the schema and property attributes of the same name. They win over what
    the Avro types imply.

    Unions of more than one type besides null, and types that refer to
    themselves, are not supported.

    Raises SchemaError when a record has no fields, or a field has no name or
    no type.

    Examples:

        ```python
        schema = AvroSchemaReader().read(
            {
                "type": "record",
                "name": "users",
                "doc": "App users",
                "fields": [
                    {"name": "id", "type": "long"},
                    {"name": "email", "type": ["null", "string"], "default": None},
                ],
            }
        )
        ```

        The schema read, as YAML:

        ```yaml
        name: users
        description: App users
        properties:
        - name: id
          logicalType: integer
          physicalType: long
          required: true
        - name: email
          logicalType: string
          physicalType: string
        ```
    """

    def read(self, record: dict[str, Any]) -> Schema:
        """
        Reads a schema from an Avro record schema, given as parsed JSON.

        Raises SchemaError when the JSON is not a record type.

        Examples:

            ```python
            schema = AvroSchemaReader().read(
                {"type": "record", "name": "users", "fields": [{"name": "id", "type": "long"}]}
            )
            schema["id"].required  # True
            ```
        """
        SchemaError.raise_if(
            not isinstance(record, dict) or record.get("type") != "record",
            "An Avro schema must be a record type",
        )

        written_record = record
        record = inline_named_types(record)
        odcs_attributes = record.get(const.ODCS_KEY) or {}
        namespace = without_none({TiozinCustomProperty.NAMESPACE: record.get("namespace")})
        record_properties = {
            key: value for key, value in record.items() if key not in const.RECORD_KEYS
        }

        schema_attributes = without_none(
            {
                "name": record.get("name"),
                "description": record.get("doc"),
                "properties": self.to_properties(AvroType(record), written_record),
                **odcs_attributes,
                "synonyms": [
                    *self.to_synonyms(record),
                    *(odcs_attributes.get("synonyms") or []),
                ]
                or None,
                "customProperties": [
                    *self.to_custom_properties(namespace),
                    *self.to_custom_properties(record_properties),
                    *(odcs_attributes.get("customProperties") or []),
                ]
                or None,
            }
        )

        name_is_unset = "name" in odcs_attributes and odcs_attributes["name"] is None
        schema_attributes = {
            key: value
            for key, value in schema_attributes.items()
            if not (key == "name" and name_is_unset)
        }

        return Schema.model_validate(schema_attributes)

    def to_properties(self, record: AvroType, written: Any = None) -> list[Property]:
        """
        Converts the fields of an Avro record to properties.

        The written record is the record as the schema writes it, with its
        references to named types, so each property keeps its type as written.
        It is the record itself when not given.

        Examples:

            ```python
            reader = AvroSchemaReader()

            reader.to_properties(
                AvroType(
                    {"type": "record", "name": "users", "fields": [{"name": "id", "type": "long"}]}
                )
            )
            # [Property(name="id", logicalType="integer", physicalType="long", required=True)]
            ```
        """
        written = record.json_value if written is None else written
        written_fields = (
            written["fields"]
            if isinstance(written, dict) and isinstance(written.get("fields"), list)
            else record.fields
        )

        return [
            self.to_property(field, record.json_value.get("name"), written_field)
            for field, written_field in zip(record.fields, written_fields, strict=True)
        ]

    def to_property(
        self,
        field: dict[str, Any],
        record_name: str,
        written_field: dict[str, Any] = None,
    ) -> Property:
        """
        Converts a field of the Avro record of the given name to a property.

        The written field is the field as the schema writes it. It is the field
        itself when not given.

        Raises SchemaError when the field has no name or no type.

        Examples:

            ```python
            reader = AvroSchemaReader()

            reader.to_property({"name": "id", "type": "long", "doc": "Identifier"}, "users")
            # Property(
            #     name="id",
            #     logicalType="integer",
            #     physicalType="long",
            #     description="Identifier",
            #     required=True,
            # )
            ```
        """
        SchemaError.raise_if(
            not isinstance(field, dict) or "name" not in field,
            f"Avro field `{field}` has no name",
        ).raise_if(
            "type" not in field,
            f"Avro field `{field['name']}` has no type",
        )

        written_field = field if written_field is None else written_field
        implied_default = (
            field.get(const.DEFAULT_PROPERTY) is None and AvroType(field["type"]).is_nullable
        )
        field_properties = {
            **{
                key: field[key]
                for key in (const.DEFAULT_PROPERTY, const.ORDER_PROPERTY)
                if key in field and not (key == const.DEFAULT_PROPERTY and implied_default)
            },
            **{key: value for key, value in field.items() if key not in const.FIELD_KEYS},
        }
        field_attributes = without_none(
            {
                "name": field["name"],
                "description": field.get("doc"),
                "synonyms": self.to_synonyms(field) or None,
                "customProperties": self.to_custom_properties(field_properties) or None,
            }
        )

        return self.read_type(
            AvroType(field["type"]),
            field_attributes,
            field.get(const.ODCS_KEY) or {},
            f"{record_name}.{field['name']}",
            written_field.get("type"),
        )

    def read_type(
        self,
        avro_type: AvroType,
        attributes: dict[str, Any],
        odcs_attributes: dict[str, Any],
        path: str,
        written: Any = None,
    ) -> Property:
        """
        Builds a property of the given Avro type with the given attributes.

        The physical type is the type exactly as the schema writes it, given as
        `written`, which may refer to named types by name. It is the type
        itself when not given.

        The odcs attributes bring back what the Avro type cannot express, and
        win over what it implies.

        The path is the name the writer gives to the type when the property
        has no `typeName`, so a type with that name gets no `typeName`.

        Examples:

            ```python
            reader = AvroSchemaReader()

            reader.read_type(AvroType(["null", "string"]), {"name": "email"}, {}, "users.email")
            # Property(name="email", logicalType="string", physicalType="string")

            reader.read_type(
                AvroType(["null", "string"]),
                {"name": "email"},
                {"classification": "pii"},
                "users.email",
            )
            # Property(
            #     name="email",
            #     logicalType="string",
            #     physicalType="string",
            #     classification="pii",
            # )
            ```
        """
        odcs_attributes = without_none(odcs_attributes)
        items_attributes = odcs_attributes.pop("items", None) or {}
        map_attributes = odcs_attributes.pop("map", None) or {}

        written_type = AvroType(avro_type.json_value if written is None else written)
        written_value = written_type.non_null.json_value
        written_definition = written_value if isinstance(written_value, dict) else {}

        value_type = avro_type.non_null
        property_attributes = {
            **attributes,
            **value_type.attributes,
            "physicalType": written_type.physical_type,
        }

        if not avro_type.is_nullable:
            property_attributes["required"] = True

        match value_type.type_name:
            case "record":
                property_attributes["properties"] = self.to_properties(
                    value_type,
                    written_definition or None,
                )
            case "array":
                property_attributes["items"] = self.read_type(
                    value_type.items,
                    {},
                    items_attributes,
                    f"{path}.items",
                    written_definition.get("items"),
                )
            case "map":
                key_attributes = map_attributes.get("key", {})
                key = (
                    {}
                    if key_attributes is None
                    else {"key": {**AvroType(const.MAP_KEY_TYPE).attributes, **key_attributes}}
                )
                property_attributes["map"] = {
                    **key,
                    "value": self.read_type(
                        value_type.values,
                        {},
                        map_attributes.get("value") or {},
                        f"{path}.values",
                        written_definition.get("values"),
                    ),
                }

        property_attributes = {**property_attributes, **odcs_attributes}

        synonyms = [
            *attributes.get("synonyms", []),
            *(odcs_attributes.get("synonyms") or []),
        ]
        custom_properties = [
            *value_type.type_parameters,
            *attributes.get("customProperties", []),
            *(
                custom_property
                for custom_property in value_type.custom_properties
                if custom_property != {"property": TiozinCustomProperty.TYPE_NAME, "value": path}
            ),
            *(odcs_attributes.get("customProperties") or []),
        ]

        return Property.model_validate(
            without_none(
                {
                    **property_attributes,
                    "synonyms": synonyms or None,
                    "customProperties": custom_properties or None,
                }
            )
        )

    @staticmethod
    def to_synonyms(named: dict[str, Any]) -> list[dict[str, Any]]:
        """
        The aliases of an Avro record or field as synonyms whose source is "avro".

        Examples:

            ```python
            AvroSchemaReader.to_synonyms({"name": "id", "aliases": ["user_id"]})
            # [{"synonym": "user_id", "source": "avro"}]
            ```
        """
        return [
            {"synonym": alias, "source": const.ALIAS_SOURCE} for alias in named.get("aliases") or []
        ]

    @staticmethod
    def to_custom_properties(values: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Custom properties with the given names and values.

        Examples:

            ```python
            AvroSchemaReader.to_custom_properties({"default": 0, "order": "descending"})
            # [
            #     {"property": "default", "value": 0},
            #     {"property": "order", "value": "descending"},
            # ]
            ```
        """
        return [{"property": name, "value": value} for name, value in values.items()]
