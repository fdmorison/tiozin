import json
from pathlib import Path

import pytest

from tiozin import Schema
from tiozin.api.metadata.schema.converters.avro import AvroSchemaConverter
from tiozin.api.metadata.schema.model import Property


def without_physical_type(value):
    """
    The dumped schema without its physical types, at every level. Read from
    Avro, the physical type is the Avro type as written, so it cannot match
    the one of the schema that was dumped.
    """
    match value:
        case dict():
            return {
                key: without_physical_type(item)
                for key, item in value.items()
                if key != "physicalType"
            }
        case list():
            return [without_physical_type(item) for item in value]
        case _:
            return value


def test_load_should_accept_json_string():
    # Arrange
    avro_schema = json.dumps(
        {
            "type": "record",
            "name": "users",
            "fields": [{"name": "id", "type": "long"}],
        }
    )

    # Act
    result = AvroSchemaConverter().load(avro_schema)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "users",
        "properties": [
            {
                "name": "id",
                "logicalType": "integer",
                "physicalType": "long",
                "logicalTypeOptions": {"format": "i64"},
                "required": True,
            }
        ],
    }
    assert actual == expected


@pytest.mark.parametrize(
    "field, expected",
    [
        (
            {"name": "email", "type": "string"},
            {"name": "email", "type": "string"},
        ),
        (
            {"name": "email", "type": ["string"]},
            {"name": "email", "type": "string"},
        ),
        (
            {"name": "email", "type": ["null", "string"]},
            {"name": "email", "type": ["null", "string"], "default": None},
        ),
        (
            {"name": "email", "type": ["null", "string"], "default": None},
            {"name": "email", "type": ["null", "string"], "default": None},
        ),
        (
            {"name": "country", "type": ["string", "null"], "default": "BR"},
            {"name": "country", "type": ["string", "null"], "default": "BR"},
        ),
    ],
    ids=[
        "plain_type",
        "single_type_union",
        "null_union",
        "null_union_with_null_default",
        "null_union_with_default",
    ],
)
def test_dump_should_write_back_field_type_and_default(field, expected):
    # Arrange
    schema = AvroSchemaConverter().load({"type": "record", "name": "users", "fields": [field]})

    # Act
    result = AvroSchemaConverter().dump(schema)

    # Assert
    actual = result["fields"][0]
    assert actual == expected


def test_load_should_restore_dumped_schema():
    # Arrange
    schema = Schema(
        name="users",
        description="Registered users",
        properties=[
            Property(name="id", logicalType="integer", physicalType="long", required=True),
            Property(
                name="name",
                logicalType="string",
                physicalType="string",
                description="Full name",
            ),
            Property(
                name="created_at",
                logicalType="timestamp",
                physicalType="long",
                required=True,
                logicalTypeOptions={"timezone": True},
                customProperties=[{"property": "timeUnit", "value": "millis"}],
            ),
            Property(
                name="address",
                logicalType="object",
                properties=[Property(name="city", logicalType="string", physicalType="string")],
            ),
            Property(
                name="tags",
                logicalType="array",
                required=True,
                items=Property(logicalType="string", physicalType="string", required=True),
            ),
        ],
    )

    # Act
    result = AvroSchemaConverter().load(AvroSchemaConverter().dump(schema))

    # Assert
    actual = without_physical_type(result.model_dump(mode="json", exclude_unset=True))
    expected = {
        "name": "users",
        "description": "Registered users",
        "properties": [
            {
                "name": "id",
                "logicalType": "integer",
                "logicalTypeOptions": {"format": "i64"},
                "required": True,
            },
            {
                "name": "name",
                "logicalType": "string",
                "description": "Full name",
            },
            {
                "name": "created_at",
                "logicalType": "timestamp",
                "required": True,
                "logicalTypeOptions": {"timezone": True},
                "customProperties": [{"property": "timeUnit", "value": "millis"}],
            },
            {
                "name": "address",
                "logicalType": "object",
                "properties": [{"name": "city", "logicalType": "string"}],
            },
            {
                "name": "tags",
                "logicalType": "array",
                "required": True,
                "items": {"logicalType": "string", "required": True},
            },
        ],
    }
    assert actual == expected


def test_load_should_restore_builder_schema_with_implied_attributes():
    # Arrange
    schema = (
        Schema(name="customers", description="Customer master data")
        .integer("id", required=True, primaryKey=True, classification="public", tags=["key"])
        .string("email", classification="pii")
        .object("address")
        .string("address.city", required=True)
        .array("friends", of="object")
        .string("friends.name")
        .array("tags", of="string")
        .map("scores", value="integer")
    )

    # Act
    result = AvroSchemaConverter().load(AvroSchemaConverter().dump(schema))

    # Assert
    actual = without_physical_type(result.model_dump(mode="json", exclude_unset=True))
    expected = {
        "name": "customers",
        "description": "Customer master data",
        "properties": [
            {
                "name": "id",
                "logicalType": "integer",
                "logicalTypeOptions": {"format": "i64"},
                "required": True,
                "primaryKey": True,
                "classification": "public",
                "tags": ["key"],
            },
            {
                "name": "email",
                "logicalType": "string",
                "classification": "pii",
            },
            {
                "name": "address",
                "logicalType": "object",
                "properties": [
                    {
                        "name": "city",
                        "logicalType": "string",
                        "required": True,
                    }
                ],
            },
            {
                "name": "friends",
                "logicalType": "array",
                "items": {
                    "logicalType": "object",
                    "properties": [{"name": "name", "logicalType": "string"}],
                },
            },
            {
                "name": "tags",
                "logicalType": "array",
                "items": {"logicalType": "string"},
            },
            {
                "name": "scores",
                "logicalType": "map",
                "map": {
                    "key": {"logicalType": "string"},
                    "value": {
                        "logicalType": "integer",
                        "logicalTypeOptions": {"format": "i64"},
                    },
                },
            },
        ],
    }
    assert actual == expected


def test_load_should_leave_name_unset_when_dumped_without_name():
    # Arrange
    schema = Schema().string("email")

    # Act
    result = AvroSchemaConverter().load(AvroSchemaConverter().dump(schema))

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {"name": "email", "logicalType": "string", "physicalType": '["null", "string"]'}
        ],
    }
    assert actual == expected


def test_load_should_restore_map_without_key():
    # Arrange
    schema = Schema(
        name="users",
        properties=[
            Property(
                name="labels",
                logicalType="map",
                required=True,
                map={
                    "value": {"logicalType": "string", "physicalType": "string", "required": True}
                },
            )
        ],
    )

    # Act
    result = AvroSchemaConverter().load(AvroSchemaConverter().dump(schema))

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "users",
        "properties": [
            {
                "name": "labels",
                "logicalType": "map",
                "physicalType": '{"type": "map", "values": "string"}',
                "required": True,
                "map": {
                    "value": {"logicalType": "string", "physicalType": "string", "required": True}
                },
            }
        ],
    }
    assert actual == expected


def test_load_should_restore_full_document():
    # Arrange
    schema = Schema.from_yaml(
        """
        name: orders
        physicalName: tb_orders
        description: Orders placed by customers
        dataGranularityDescription: One row per order
        tags: [sales]
        synonyms:
          - synonym: purchases
        authoritativeDefinitions:
          - url: https://example.com/orders
            type: businessDefinition
        customProperties:
          - property: owner
            value: sales
        context:
          instructions: Use for revenue questions
        relationships:
          - from: orders.customer_id
            to: customers.id
        quality:
          - type: library
            metric: rowCount
            mustBeGreaterThan: 0
        properties:
          - name: id
            logicalType: integer
            physicalType: bigint
            required: true
            primaryKey: true
            primaryKeyPosition: 1
            logicalTypeOptions:
              format: i64
              minimum: 1
          - name: customer_id
            logicalType: integer
            physicalType: long
            logicalTypeOptions:
              format: i64
            required: false
            relationships:
              - to: customers.id
          - name: status
            logicalType: string
            physicalType: enum
            enum:
              - value: open
                label: Open
              - value: closed
            examples: [open]
          - name: price
            logicalType: number
            physicalType: bytes
            customProperties:
              - property: precision
                value: 10
              - property: scale
                value: 2
          - name: created
            logicalType: timestamp
            physicalType: long
            logicalTypeOptions:
              timezone: true
            customProperties:
              - property: timeUnit
                value: millis
          - name: items
            logicalType: array
            classification: internal
            items:
              logicalType: object
              description: One item
              properties:
                - name: sku
                  logicalType: string
                  physicalType: string
                  classification: public
                  unique: true
          - name: attributes
            logicalType: map
            map:
              key:
                logicalType: string
                physicalType: string
                required: true
                description: Attribute name
              value:
                logicalType: string
                physicalType: string
                classification: pii
          - name: address
            logicalType: object
            properties:
              - name: city
                logicalType: string
                physicalType: string
        """
    )

    # Act
    result = AvroSchemaConverter().load(AvroSchemaConverter().dump(schema))

    # Assert
    actual = without_physical_type(result.model_dump(mode="json", exclude_unset=True))
    expected = without_physical_type(schema.model_dump(mode="json", exclude_unset=True))
    assert actual == expected


def test_load_should_restore_custom_properties_avro_writes_under_odcs():
    # Arrange
    schema = Schema(name="users").string(
        "email",
        required=True,
        customProperties=[
            {"property": "namespace", "value": "com.acme"},
            {"property": "typeName", "value": "Email"},
        ],
    )

    # Act
    result = AvroSchemaConverter().load(AvroSchemaConverter().dump(schema))

    # Assert
    actual = result["email"].model_dump(exclude_unset=True)
    expected = {
        "name": "email",
        "logicalType": "string",
        "physicalType": "string",
        "required": True,
        "customProperties": [
            {"property": "typeName", "value": "Email"},
            {"property": "namespace", "value": "com.acme"},
        ],
    }
    assert actual == expected


@pytest.mark.parametrize(
    "schema_file",
    [
        "avro_record_with_logical_types.json",
        "avro_record_with_nested_types.json",
        "avro_record_with_named_types.json",
        "avro_record_with_extra_attributes.json",
        "avro_record_with_fixed_decimal.json",
    ],
)
def test_load_should_round_trip_avro_schema(schema_file):
    # Arrange
    avro_schema = json.loads(Path(f"tests/mocks/schemas/{schema_file}").read_text())

    # Act
    result = AvroSchemaConverter().dump(AvroSchemaConverter().load(avro_schema))

    # Assert
    actual = result
    expected = avro_schema
    assert actual == expected


def test_load_should_restore_schema_read_from_avro():
    # Arrange
    schema = Schema.from_avro(
        json.loads(Path("tests/mocks/schemas/avro_record_with_named_types.json").read_text())
    )

    # Act
    result = AvroSchemaConverter().load(AvroSchemaConverter().dump(schema))

    # Assert
    actual = result
    expected = schema
    assert actual == expected


def test_dump_should_ignore_unknown_options():
    # Arrange
    schema = Schema(name="users").string("name")

    # Act
    result = AvroSchemaConverter().dump(schema, version="4.1")

    # Assert
    actual = result
    expected = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "name", "type": ["null", "string"], "default": None}],
    }
    assert actual == expected


def test_load_should_ignore_unknown_options():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "id", "type": "long"}],
    }

    # Act
    result = AvroSchemaConverter().load(avro_schema, version="4.1")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "users",
        "properties": [
            {
                "name": "id",
                "logicalType": "integer",
                "physicalType": "long",
                "logicalTypeOptions": {"format": "i64"},
                "required": True,
            }
        ],
    }
    assert actual == expected
