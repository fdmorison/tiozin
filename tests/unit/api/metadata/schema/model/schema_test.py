import json
from pathlib import Path

import jsonschema
import pytest

from tiozin import Schema
from tiozin.api.metadata.schema.model import Context, Property
from tiozin.exceptions import PropertyNotFoundError, SchemaError


def test_add_should_add_property():
    # Arrange
    schema = Schema(name="users")

    # Act
    schema.add("name", "string")

    # Assert
    actual = schema.model_dump(exclude_unset=True)
    expected = {
        "name": "users",
        "properties": [{"name": "name", "logicalType": "string"}],
    }
    assert actual == expected


def test_add_should_return_same_schema():
    # Arrange
    schema = Schema(name="users")

    # Act
    result = schema.add("name", "string")

    # Assert
    assert result is schema


def test_add_should_set_attributes():
    # Arrange
    schema = Schema(name="users")

    # Act
    schema.add("email", "string", required=True, description="Email address")

    # Assert
    actual = schema.model_dump(exclude_unset=True)
    expected = {
        "name": "users",
        "properties": [
            {
                "name": "email",
                "logicalType": "string",
                "required": True,
                "description": "Email address",
            }
        ],
    }
    assert actual == expected


def test_add_should_add_property_inside_object():
    # Arrange
    schema = Schema(name="users").object("profile")

    # Act
    schema.add("profile.age", "integer")

    # Assert
    actual = list(schema.flatten())
    expected = ["profile", "profile.age"]
    assert actual == expected


def test_add_should_raise_schema_error_when_name_exists_ignoring_case():
    # Arrange
    schema = Schema(name="users").string("name")

    # Act / Assert
    with pytest.raises(SchemaError):
        schema.add("NAME", "string")


def test_add_should_raise_property_not_found_when_parent_does_not_exist():
    # Arrange
    schema = Schema(name="users")

    # Act / Assert
    with pytest.raises(PropertyNotFoundError):
        schema.add("profile.age", "integer")


def test_add_should_raise_schema_error_when_parent_cannot_hold_properties():
    # Arrange
    schema = Schema(name="users").string("name")

    # Act / Assert
    with pytest.raises(SchemaError):
        schema.add("name.first", "string")


@pytest.mark.parametrize(
    "builder, expected",
    [
        (Schema.string, "string"),
        (Schema.integer, "integer"),
        (Schema.number, "number"),
        (Schema.boolean, "boolean"),
        (Schema.date, "date"),
        (Schema.timestamp, "timestamp"),
        (Schema.time, "time"),
        (Schema.object, "object"),
    ],
)
def test_builder_should_add_property_of_its_type(builder, expected):
    # Arrange
    schema = Schema(name="users")

    # Act
    builder(schema, "field")

    # Assert
    actual = schema["field"].logicalType
    assert actual == expected


def test_array_should_add_array_of_given_type():
    # Arrange
    schema = Schema(name="users")

    # Act
    schema.array("tags", of="string")

    # Assert
    actual = schema.model_dump(exclude_unset=True)
    expected = {
        "name": "users",
        "properties": [
            {"name": "tags", "logicalType": "array", "items": {"logicalType": "string"}},
        ],
    }
    assert actual == expected


def test_map_should_add_map_with_string_keys():
    # Arrange
    schema = Schema(name="users")

    # Act
    schema.map("attributes", value="integer")

    # Assert
    actual = schema.model_dump(exclude_unset=True)
    expected = {
        "name": "users",
        "properties": [
            {
                "name": "attributes",
                "logicalType": "map",
                "map": {
                    "key": {"logicalType": "string"},
                    "value": {"logicalType": "integer"},
                },
            },
        ],
    }
    assert actual == expected


def test_map_should_add_map_with_given_key_type():
    # Arrange
    schema = Schema(name="users")

    # Act
    schema.map("scores", value="number", key="integer")

    # Assert
    actual = schema["scores"].map.key.logicalType
    expected = "integer"
    assert actual == expected


def test_schema_should_raise_schema_error_when_built_with_duplicate_names():
    # Act / Assert
    with pytest.raises(SchemaError):
        Schema(
            name="users",
            properties=[
                Property(name="name", logicalType="string"),
                Property(name="Name", logicalType="string"),
            ],
        )


def test_getitem_should_return_property_at_path():
    # Arrange
    schema = Schema(name="users").object("profile").integer("profile.age")

    # Act
    result = schema["profile.age"]

    # Assert
    actual = (
        result.name,
        result.logicalType,
    )
    expected = (
        "age",
        "integer",
    )
    assert actual == expected


def test_getitem_should_ignore_case():
    # Arrange
    schema = Schema(name="users").object("profile").integer("profile.age")

    # Act
    result = schema["PROFILE.Age"]

    # Assert
    actual = result.name
    expected = "age"
    assert actual == expected


def test_getitem_should_accept_sequence_of_names():
    # Arrange
    schema = Schema(name="users").object("profile").integer("profile.age")

    # Act
    result = schema[["profile", "age"]]

    # Assert
    actual = result.name
    expected = "age"
    assert actual == expected


@pytest.mark.parametrize(
    "path",
    [
        "friends.name",
        "attributes.color",
    ],
)
def test_getitem_should_go_through_arrays_and_maps(path):
    # Arrange
    schema = (
        Schema(name="users")
        .array("friends", of="object")
        .string("friends.name")
        .map("attributes", value="object")
        .string("attributes.color")
    )

    # Act
    result = schema[path]

    # Assert
    actual = result.logicalType
    expected = "string"
    assert actual == expected


def test_getitem_should_raise_property_not_found_when_path_does_not_exist():
    # Arrange
    schema = Schema(name="users").string("name")

    # Act / Assert
    with pytest.raises(PropertyNotFoundError):
        schema["email"]


def test_contains_should_pass_when_path_exists():
    # Arrange
    schema = Schema(name="users").array("friends", of="object").string("friends.name")

    # Act / Assert
    assert "FRIENDS.name" in schema


def test_contains_should_not_pass_when_path_does_not_exist():
    # Arrange
    schema = Schema(name="users").array("friends", of="object").string("friends.name")

    # Act / Assert
    assert "friends.email" not in schema


def test_remove_should_remove_property():
    # Arrange
    schema = Schema(name="users").string("name").string("email")

    # Act
    schema.remove("email")

    # Assert
    actual = list(schema.flatten())
    expected = ["name"]
    assert actual == expected


def test_remove_should_return_same_schema():
    # Arrange
    schema = Schema(name="users").string("name")

    # Act
    result = schema.remove("name")

    # Assert
    assert result is schema


def test_remove_should_remove_nested_property():
    # Arrange
    schema = Schema(name="users").object("profile").integer("profile.age").string("profile.city")

    # Act
    schema.remove("profile.age")

    # Assert
    actual = list(schema.flatten())
    expected = ["profile", "profile.city"]
    assert actual == expected


def test_remove_should_raise_property_not_found_when_path_does_not_exist():
    # Arrange
    schema = Schema(name="users").string("name")

    # Act / Assert
    with pytest.raises(PropertyNotFoundError):
        schema.remove("email")


def test_flatten_should_return_properties_by_path_with_parents_first():
    # Arrange
    schema = (
        Schema(name="users")
        .string("name")
        .object("profile")
        .integer("profile.age")
        .array("friends", of="object")
        .string("friends.name")
    )

    # Act
    result = schema.flatten()

    # Assert
    actual = list(result)
    expected = ["name", "profile", "profile.age", "friends", "friends.name"]
    assert actual == expected


def test_sort_should_sort_properties_by_name_ignoring_case_at_every_level():
    # Arrange
    schema = (
        Schema(name="users")
        .string("name")
        .object("Address")
        .string("Address.zip")
        .string("Address.City")
    )

    # Act
    result = schema.sort()

    # Assert
    actual = (
        result is schema,
        list(schema.flatten()),
    )
    expected = (
        True,
        ["Address", "Address.City", "Address.zip", "name"],
    )
    assert actual == expected


def test_normalize_field_names_should_rename_properties_to_snake_case_by_default():
    # Arrange
    schema = Schema(name="users").object("HomeAddress").string("HomeAddress.ZipCode")

    # Act
    result = schema.normalize_field_names()

    # Assert
    actual = (
        result is schema,
        list(schema.flatten()),
    )
    expected = (
        True,
        ["home_address", "home_address.zip_code"],
    )
    assert actual == expected


def test_normalize_field_names_should_rename_properties_to_given_case():
    # Arrange
    schema = Schema(name="users").object("home_address").string("home_address.zip_code")

    # Act
    schema.normalize_field_names("camel")

    # Assert
    actual = list(schema.flatten())
    expected = ["homeAddress", "homeAddress.zipCode"]
    assert actual == expected


def test_normalize_field_names_should_preserve_schema_name():
    # Arrange
    schema = Schema(name="orders.created.v1").string("First Name")

    # Act
    result = schema.normalize_field_names()

    # Assert
    actual = result.name
    expected = "orders.created.v1"
    assert actual == expected


def test_normalize_field_names_should_raise_schema_error_when_case_is_unknown():
    # Arrange
    schema = Schema(name="users").string("FirstName")

    # Act / Assert
    with pytest.raises(SchemaError):
        schema.normalize_field_names("title")


@pytest.mark.parametrize(
    "first, second, duplicate",
    [
        ("FirstName", "first_name", "first_name"),
        ("%", "$", "_"),
    ],
)
def test_normalize_field_names_should_raise_schema_error_when_siblings_collide(
    first, second, duplicate
):
    # Arrange
    schema = Schema(name="users").string(first).string(second)

    # Act / Assert
    with pytest.raises(SchemaError, match=f"Duplicate property `{duplicate}`"):
        schema.normalize_field_names()


def test_root_should_hold_schema_properties_as_object():
    # Arrange
    schema = Schema(name="users").string("name")

    # Act
    result = schema.root

    # Assert
    actual = (
        result.logicalType,
        [child.name for child in result.children()],
    )
    expected = (
        "object",
        ["name"],
    )
    assert actual == expected


def test_root_should_edit_schema():
    # Arrange
    schema = Schema(name="users")

    # Act
    schema.root.add(Property(name="name", logicalType="string"))

    # Assert
    actual = list(schema.flatten())
    expected = ["name"]
    assert actual == expected


def test_clone_should_copy_schema():
    # Arrange
    schema = Schema(name="users").object("profile").integer("profile.age")

    # Act
    result = schema.clone()

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "users",
        "properties": [
            {
                "name": "profile",
                "logicalType": "object",
                "properties": [{"name": "age", "logicalType": "integer"}],
            }
        ],
    }
    assert actual == expected


def test_clone_should_be_independent_from_original():
    # Arrange
    schema = Schema(name="users").object("profile").integer("profile.age")

    # Act
    result = schema.clone()
    result.remove("profile.age")

    # Assert
    actual = list(schema.flatten())
    expected = ["profile", "profile.age"]
    assert actual == expected


def test_rename_should_change_name():
    # Arrange
    schema = Schema(name="users")

    # Act
    result = schema.rename("customers")

    # Assert
    actual = (
        result is schema,
        schema.name,
    )
    expected = (
        True,
        "customers",
    )
    assert actual == expected


def test_show_should_print_schema_as_yaml(capsys):
    # Arrange
    schema = Schema(name="users").string("name", required=True)

    # Act
    schema.show()

    # Assert
    actual = capsys.readouterr().out
    expected = "name: users\nproperties:\n- name: name\n  logicalType: string\n  required: true\n\n"
    assert actual == expected


def test_show_should_color_yaml_with_solarized_dark_by_default(capsys, monkeypatch):
    # Arrange
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.setenv("COLORTERM", "truecolor")
    schema = Schema(name="customers")

    # Act
    schema.show()

    # Assert
    actual = capsys.readouterr().out
    expected = (
        "\x1b[38;2;38;139;210;49mname\x1b[0m"
        "\x1b[38;2;131;148;150;49m:\x1b[0m"
        "\x1b[38;2;131;148;150;49m \x1b[0m"
        "\x1b[38;2;42;161;152;49mcustomers\x1b[0m\n\n"
    )
    assert actual == expected


@pytest.mark.parametrize(
    "theme, expected",
    [
        (
            "dracula",
            "\x1b[38;2;255;121;198;49mname\x1b[0m"
            "\x1b[38;2;248;248;242;49m:\x1b[0m"
            "\x1b[38;2;248;248;242;49m \x1b[0m"
            "\x1b[38;2;189;147;249;49mcustomers\x1b[0m\n\n",
        ),
        (
            "ansi_dark",
            "\x1b[94;49mname\x1b[0m"
            "\x1b[49m:\x1b[0m"
            "\x1b[90;49m \x1b[0m"
            "\x1b[33;49mcustomers\x1b[0m\n\n",
        ),
    ],
)
def test_show_should_color_yaml_with_given_theme(capsys, monkeypatch, theme, expected):
    # Arrange
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.setenv("COLORTERM", "truecolor")
    schema = Schema(name="customers")

    # Act
    schema.show(theme)

    # Assert
    actual = capsys.readouterr().out
    assert actual == expected


@pytest.mark.parametrize("theme", ["dracula", "solarized-light"])
def test_show_should_print_plain_yaml_without_color_for_any_theme(capsys, monkeypatch, theme):
    # Arrange
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    schema = Schema(name="customers")

    # Act
    schema.show(theme)

    # Assert
    actual = capsys.readouterr().out
    expected = "name: customers\n\n"
    assert actual == expected


def test_show_should_raise_schema_error_when_theme_is_unknown():
    # Arrange
    schema = Schema(name="customers")

    # Act / Assert
    with pytest.raises(SchemaError, match="Invalid value 'draculaa'. Must be one of:"):
        schema.show("draculaa")


def test_evolve_should_add_observed_property_as_optional():
    # Arrange
    contract = Schema(name="contract").string("id", required=True)
    observed = Schema(name="observed").string("id").string("email", required=True)

    # Act
    result = contract.evolve(observed)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "contract",
        "properties": [
            {"name": "id", "logicalType": "string", "required": True},
            {"name": "email", "logicalType": "string", "required": False},
        ],
    }
    assert actual == expected


def test_document_from_should_copy_contract_documentation():
    # Arrange
    observed = Schema(name="observed").integer("id")
    contract = Schema(name="contract").string("id", description="Customer identifier")

    # Act
    result = observed.document_from(contract)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "observed",
        "properties": [
            {"name": "id", "logicalType": "integer", "description": "Customer identifier"},
        ],
    }
    assert actual == expected


def test_to_format_should_convert_schema_to_format():
    # Arrange
    schema = Schema(name="users").integer("id", physicalType="long", required=True)

    # Act
    result = schema.to_format("spark")

    # Assert
    actual = result
    expected = {
        "type": "struct",
        "fields": [{"name": "id", "type": "long", "nullable": False, "metadata": {}}],
        "metadata": {"name": "users"},
    }
    assert actual == expected


def test_to_format_should_pass_options_to_format():
    # Arrange
    schema = Schema(name="users").time("starts_at")

    # Act
    result = schema.to_format("spark", version="4.1")

    # Assert
    actual = result
    expected = {
        "type": "struct",
        "fields": [{"name": "starts_at", "type": "time(6)", "nullable": True, "metadata": {}}],
        "metadata": {"name": "users"},
    }
    assert actual == expected


def test_to_format_should_raise_schema_error_when_format_is_unsupported():
    # Arrange
    schema = Schema(name="users").string("name")

    # Act / Assert
    with pytest.raises(SchemaError):
        schema.to_format("protobuf")


def test_from_format_should_create_schema_from_format():
    # Arrange
    spark_schema = {
        "type": "struct",
        "fields": [{"name": "id", "type": "long", "nullable": False, "metadata": {}}],
    }

    # Act
    result = Schema.from_format("spark", spark_schema)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {
                "name": "id",
                "logicalType": "integer",
                "physicalType": "long",
                "logicalTypeOptions": {"format": "i64"},
                "required": True,
            },
        ],
    }
    assert actual == expected


def test_from_format_should_raise_schema_error_when_format_is_unsupported():
    # Act / Assert
    with pytest.raises(SchemaError):
        Schema.from_format("protobuf", {})


def test_to_spark_should_convert_schema_to_spark():
    # Arrange
    schema = Schema(name="users").string("name", physicalType="string")

    # Act
    result = schema.to_spark()

    # Assert
    actual = result
    expected = {
        "type": "struct",
        "fields": [{"name": "name", "type": "string", "nullable": True, "metadata": {}}],
        "metadata": {"name": "users"},
    }
    assert actual == expected


def test_to_spark_should_target_given_spark_version():
    # Arrange
    schema = Schema(name="users").time("starts_at")

    # Act
    result = schema.to_spark(version="4.1")

    # Assert
    actual = result
    expected = {
        "type": "struct",
        "fields": [{"name": "starts_at", "type": "time(6)", "nullable": True, "metadata": {}}],
        "metadata": {"name": "users"},
    }
    assert actual == expected


def test_to_spark_should_write_time_as_timestamp_ntz_when_target_version_has_no_time_type():
    # Arrange
    schema = Schema(name="users").time("starts_at")

    # Act
    result = schema.to_spark(version="3.5")

    # Assert
    actual = result
    expected = {
        "type": "struct",
        "fields": [
            {
                "name": "starts_at",
                "type": "timestamp_ntz",
                "nullable": True,
                "metadata": {"logicalType": "time"},
            }
        ],
        "metadata": {"name": "users"},
    }
    assert actual == expected


def test_from_spark_should_create_schema_from_spark():
    # Arrange
    spark_schema = {
        "type": "struct",
        "fields": [{"name": "name", "type": "string", "nullable": True, "metadata": {}}],
    }

    # Act
    result = Schema.from_spark(spark_schema)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "properties": [{"name": "name", "logicalType": "string", "physicalType": "string"}],
    }
    assert actual == expected


def test_from_spark_should_ignore_unknown_options():
    # Arrange
    spark_schema = {
        "type": "struct",
        "fields": [{"name": "name", "type": "string", "nullable": True, "metadata": {}}],
    }

    # Act
    result = Schema.from_spark(spark_schema, unknown_option="ignored")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "properties": [{"name": "name", "logicalType": "string", "physicalType": "string"}],
    }
    assert actual == expected


def test_to_avro_should_convert_schema_to_avro():
    # Arrange
    schema = Schema(name="users").string("name")

    # Act
    result = schema.to_avro()

    # Assert
    actual = result
    expected = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "name", "type": ["null", "string"], "default": None}],
    }
    assert actual == expected


def test_to_avro_should_ignore_unknown_options():
    # Arrange
    schema = Schema(name="users").string("name")

    # Act
    result = schema.to_avro(unknown_option="ignored")

    # Assert
    actual = result
    expected = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "name", "type": ["null", "string"], "default": None}],
    }
    assert actual == expected


def test_from_avro_should_create_schema_from_avro():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "name", "type": ["null", "string"], "default": None}],
    }

    # Act
    result = Schema.from_avro(avro_schema)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "users",
        "properties": [
            {"name": "name", "logicalType": "string", "physicalType": '["null", "string"]'}
        ],
    }
    assert actual == expected


def test_from_avro_should_ignore_unknown_options():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "name", "type": ["null", "string"], "default": None}],
    }

    # Act
    result = Schema.from_avro(avro_schema, unknown_option="ignored")

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "users",
        "properties": [
            {"name": "name", "logicalType": "string", "physicalType": '["null", "string"]'}
        ],
    }
    assert actual == expected


def test_from_file_should_load_schema_written_by_to_yaml(tmp_path):
    # Arrange
    schema = (
        Schema(name="users", description="Registered users")
        .string("name", required=True)
        .array("friends", of="object")
        .string("friends.name", classification="pii")
        .map("attributes", value="integer")
    )
    path = tmp_path / "users.yaml"
    path.write_text(schema.to_yaml())

    # Act
    result = Schema.from_file(str(path))

    # Assert
    actual = result
    expected = (
        Schema(name="users", description="Registered users")
        .string("name", required=True)
        .array("friends", of="object")
        .string("friends.name", classification="pii")
        .map("attributes", value="integer")
    )
    assert actual == expected


def test_schema_should_default_physical_type_to_table():
    # Act
    result = Schema(name="orders")

    # Assert
    actual = result.physicalType
    expected = "table"
    assert actual == expected


def test_to_yaml_should_write_only_set_attributes():
    # Arrange
    schema = Schema(name="orders").integer("id")

    # Act
    result = schema.to_yaml()

    # Assert
    actual = result
    expected = "name: orders\nproperties:\n- name: id\n  logicalType: integer\n"
    assert actual == expected


def test_to_yaml_should_write_only_set_options():
    # Arrange
    schema = Schema(name="orders").integer("id", logicalTypeOptions={"minimum": 1})

    # Act
    result = schema.to_yaml()

    # Assert
    actual = result
    expected = (
        "name: orders\n"
        "properties:\n"
        "- name: id\n"
        "  logicalType: integer\n"
        "  logicalTypeOptions:\n"
        "    minimum: 1\n"
    )
    assert actual == expected


@pytest.mark.parametrize(
    "context, expected",
    [
        ("Use for revenue questions", "Use for revenue questions"),
        (
            {"instructions": "Use for revenue questions"},
            Context(instructions="Use for revenue questions"),
        ),
    ],
    ids=["text", "object"],
)
def test_schema_should_accept_context_as_text_or_object(context, expected):
    # Act
    result = Schema(name="orders", context=context)

    # Assert
    actual = result.context
    assert actual == expected


def test_to_yaml_should_round_trip_full_document():
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
          verifiedStatements:
            - question: How many orders?
              answer: Count the rows
          constraints:
            - constraint: Do not expose customer_id
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
            relationships:
              - to: customers.id
            quality:
              - type: sql
                query: select count(*) from orders where customer_id is null
                mustBe: 0
          - name: status
            logicalType: string
            enum:
              - value: open
                label: Open
              - value: closed
            examples: [open]
          - name: items
            logicalType: array
            logicalTypeOptions:
              minItems: 1
            items:
              logicalType: object
              properties:
                - name: sku
                  logicalType: string
          - name: attributes
            logicalType: map
            map:
              key:
                logicalType: string
              value:
                logicalType: string
        """
    )

    # Act
    result = Schema.from_yaml(schema.to_yaml())

    # Assert
    actual = result
    expected = schema
    assert actual == expected


def test_model_dump_should_write_back_odcs_document():
    # Arrange
    odcs_schema = {
        "name": "orders",
        "physicalName": "tb_orders",
        "description": "Orders placed by customers",
        "tags": ["sales"],
        "synonyms": [{"synonym": "purchases"}],
        "authoritativeDefinitions": [
            {"url": "https://example.com/orders", "type": "businessDefinition"}
        ],
        "customProperties": [{"property": "owner", "value": "sales"}],
        "context": {"instructions": "Use for revenue questions"},
        "relationships": [{"from": "orders.customer_id", "to": "customers.id"}],
        "quality": [{"type": "library", "metric": "rowCount", "mustBeGreaterThan": 0}],
        "properties": [
            {
                "name": "id",
                "logicalType": "integer",
                "physicalType": "bigint",
                "required": True,
                "primaryKey": True,
                "primaryKeyPosition": 1,
                "logicalTypeOptions": {"format": "i64", "minimum": 1},
            },
            {
                "name": "customer_id",
                "logicalType": "integer",
                "relationships": [{"to": "customers.id"}],
            },
            {
                "name": "status",
                "logicalType": "string",
                "enum": [{"value": "open", "label": "Open"}, {"value": "closed"}],
            },
            {
                "name": "items",
                "logicalType": "array",
                "items": {
                    "logicalType": "object",
                    "properties": [{"name": "sku", "logicalType": "string"}],
                },
            },
            {
                "name": "attributes",
                "logicalType": "map",
                "map": {"key": {"logicalType": "string"}, "value": {"logicalType": "string"}},
            },
        ],
    }
    schema = Schema.model_validate(odcs_schema)

    # Act
    result = schema.model_dump(mode="json", exclude_unset=True)

    # Assert
    actual = result
    expected = {
        "name": "orders",
        "physicalName": "tb_orders",
        "description": "Orders placed by customers",
        "tags": ["sales"],
        "synonyms": [{"synonym": "purchases"}],
        "authoritativeDefinitions": [
            {"url": "https://example.com/orders", "type": "businessDefinition"}
        ],
        "customProperties": [{"property": "owner", "value": "sales"}],
        "context": {"instructions": "Use for revenue questions"},
        "relationships": [{"from": "orders.customer_id", "to": "customers.id"}],
        "quality": [{"type": "library", "metric": "rowCount", "mustBeGreaterThan": 0}],
        "properties": [
            {
                "name": "id",
                "logicalType": "integer",
                "physicalType": "bigint",
                "required": True,
                "primaryKey": True,
                "primaryKeyPosition": 1,
                "logicalTypeOptions": {"format": "i64", "minimum": 1},
            },
            {
                "name": "customer_id",
                "logicalType": "integer",
                "relationships": [{"to": "customers.id"}],
            },
            {
                "name": "status",
                "logicalType": "string",
                "enum": [{"value": "open", "label": "Open"}, {"value": "closed"}],
            },
            {
                "name": "items",
                "logicalType": "array",
                "items": {
                    "logicalType": "object",
                    "properties": [{"name": "sku", "logicalType": "string"}],
                },
            },
            {
                "name": "attributes",
                "logicalType": "map",
                "map": {"key": {"logicalType": "string"}, "value": {"logicalType": "string"}},
            },
        ],
    }
    assert actual == expected


def test_model_dump_should_conform_to_odcs_schema_object():
    # Arrange
    spec = json.loads(Path("tests/mocks/schemas/odcs-json-schema-v3.2.0.json").read_text())
    validator = jsonschema.Draft201909Validator(
        {"$ref": "#/$defs/SchemaObject", "$defs": spec["$defs"]}
    )
    schema = (
        Schema(name="customers")
        .integer("id", required=True)
        .string("name")
        .object("address")
        .string("address.city")
        .array("tags", of="string")
        .map("scores", value="integer")
    )

    # Act
    result = schema.model_dump(mode="json", exclude_unset=True)

    # Assert
    actual = [error.message for error in validator.iter_errors(result)]
    expected = []
    assert actual == expected


def test_model_dump_should_conform_to_odcs_schema_object_with_every_section():
    # Arrange
    spec = json.loads(Path("tests/mocks/schemas/odcs-json-schema-v3.2.0.json").read_text())
    validator = jsonschema.Draft201909Validator(
        {"$ref": "#/$defs/SchemaObject", "$defs": spec["$defs"]}
    )
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
          verifiedStatements:
            - question: How many orders?
              answer: Count the rows
          constraints:
            - constraint: Do not expose customer_id
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
            relationships:
              - to: customers.id
            quality:
              - type: sql
                query: select count(*) from orders where customer_id is null
                mustBe: 0
          - name: status
            logicalType: string
            enum:
              - value: open
                label: Open
              - value: closed
            examples: [open]
          - name: items
            logicalType: array
            logicalTypeOptions:
              minItems: 1
            items:
              logicalType: object
              properties:
                - name: sku
                  logicalType: string
          - name: attributes
            logicalType: map
            map:
              key:
                logicalType: string
              value:
                logicalType: string
        """
    )

    # Act
    result = schema.model_dump(mode="json", exclude_unset=True)

    # Assert
    actual = [error.message for error in validator.iter_errors(result)]
    expected = []
    assert actual == expected


def test_schema_should_write_namespace_as_custom_property():
    # Arrange
    schema = Schema(name="users", namespace="com.acme")

    # Act
    result = schema.model_dump(mode="json", exclude_unset=True)

    # Assert
    actual = result
    expected = {
        "name": "users",
        "customProperties": [{"property": "namespace", "value": "com.acme"}],
    }
    assert actual == expected


def test_schema_should_take_namespace_from_custom_property():
    # Act
    result = Schema(
        name="users",
        customProperties=[{"property": "namespace", "value": "com.acme"}],
    )

    # Assert
    actual = result.namespace
    expected = "com.acme"
    assert actual == expected


def test_model_dump_should_write_convention_fields_of_properties_once():
    # Arrange
    schema = Schema(name="users").object("address", typeName="Address")

    # Act
    result = schema.model_dump(mode="json", exclude_unset=True)

    # Assert
    actual = result
    expected = {
        "name": "users",
        "properties": [
            {
                "name": "address",
                "logicalType": "object",
                "customProperties": [{"property": "typeName", "value": "Address"}],
            }
        ],
    }
    assert actual == expected


def test_schema_should_raise_schema_error_when_relationship_lacks_from():
    # Act / Assert
    with pytest.raises(SchemaError, match="A schema relationship needs both `from` and `to`"):
        Schema(name="orders", relationships=[{"to": "customers.id"}])
