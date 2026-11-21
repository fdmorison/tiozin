import pytest

from tiozin import Schema
from tiozin.api.metadata.schema.converters.avro import AvroSchemaWriter
from tiozin.api.metadata.schema.model import Map, Property
from tiozin.exceptions import SchemaError


def test_write_should_write_record_field_per_property():
    # Arrange
    schema = Schema(name="users").string("name", required=True)

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "name", "type": "string"}],
    }
    assert actual == expected


def test_write_should_write_optional_property_as_null_union_defaulting_to_null():
    # Arrange
    schema = Schema(name="users").string("name")

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]
    expected = {"name": "name", "type": ["null", "string"], "default": None}
    assert actual == expected


def test_write_should_write_property_description_as_doc():
    # Arrange
    schema = Schema(name="users").string("name", required=True, description="Full name")

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]
    expected = {"name": "name", "type": "string", "doc": "Full name"}
    assert actual == expected


def test_write_should_write_schema_description_as_doc():
    # Arrange
    schema = Schema(name="users", description="Registered users").string("name", required=True)

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "name", "type": "string"}],
        "doc": "Registered users",
    }
    assert actual == expected


def test_write_should_name_record_root_and_mark_name_unset_when_schema_has_no_name():
    # Arrange
    schema = Schema().string("name", required=True)

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {
        "type": "record",
        "name": "root",
        "fields": [{"name": "name", "type": "string"}],
        "odcs": {"name": None},
    }
    assert actual == expected


def test_write_should_accept_dotted_schema_name():
    # Arrange
    schema = Schema(name="ns.users").string("name", required=True)

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {
        "type": "record",
        "name": "ns.users",
        "fields": [{"name": "name", "type": "string"}],
    }
    assert actual == expected


@pytest.mark.parametrize(
    "logical_type, expected",
    [
        ("string", "string"),
        ("integer", "long"),
        ("number", "double"),
        ("boolean", "boolean"),
        ("date", {"type": "int", "logicalType": "date"}),
        ("timestamp", {"type": "long", "logicalType": "timestamp-micros"}),
        ("time", {"type": "long", "logicalType": "time-micros"}),
    ],
)
def test_write_should_pick_avro_type_from_logical_type(logical_type, expected):
    # Arrange
    schema = Schema(name="users").add("field", logical_type, required=True)

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]["type"]
    assert actual == expected


@pytest.mark.parametrize(
    "logical_type, physical_type, expected",
    [
        ("integer", "string", "long"),
        ("integer", "int", "long"),
        ("integer", "bigint", "long"),
        ("number", "float", "double"),
        ("number", "decimal(10,2)", "double"),
        ("string", "bytes", "string"),
        ("string", "fixed(16)", "string"),
        ("string", "uuid", "string"),
        ("string", "varchar(10)", "string"),
        ("time", "time-millis", {"type": "long", "logicalType": "time-micros"}),
        ("timestamp", "timestamp-millis", {"type": "long", "logicalType": "timestamp-micros"}),
        (
            "timestamp",
            "local-timestamp-micros",
            {"type": "long", "logicalType": "timestamp-micros"},
        ),
    ],
)
def test_write_should_ignore_physical_type_when_picking_avro_type(
    logical_type, physical_type, expected
):
    # Arrange
    schema = Schema(name="users").add(
        "field", logical_type, physicalType=physical_type, required=True
    )

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]["type"]
    assert actual == expected


@pytest.mark.parametrize(
    "prop",
    [
        Property(name="id", logicalType="integer", physicalType="bigint", required=True),
        Property(name="id", logicalType="integer", physicalType="int", required=True),
        Property(name="id", logicalType="integer", physicalType="decimal(10,0)", required=True),
    ],
    ids=["bigint", "int", "decimal"],
)
def test_write_should_not_write_property_physical_type(prop):
    # Arrange
    schema = Schema(name="users", properties=[prop])

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]
    expected = {"name": "id", "type": "long"}
    assert actual == expected


def test_write_should_write_schema_physical_type_under_odcs():
    # Arrange
    schema = Schema(name="users", physicalType="view").string("email", required=True)

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "email", "type": "string"}],
        "odcs": {"physicalType": "view"},
    }
    assert actual == expected


@pytest.mark.parametrize(
    "logical_type, size_format, expected",
    [
        ("integer", "i8", "int"),
        ("integer", "i16", "int"),
        ("integer", "i32", "int"),
        ("integer", "u8", "int"),
        ("integer", "u16", "int"),
        ("integer", "i64", "long"),
        ("integer", "u32", "long"),
        ("number", "f32", "float"),
        ("number", "f64", "double"),
    ],
)
def test_write_should_pick_avro_size_from_format(logical_type, size_format, expected):
    # Arrange
    schema = Schema(name="users").add(
        "field", logical_type, required=True, logicalTypeOptions={"format": size_format}
    )

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]["type"]
    assert actual == expected


@pytest.mark.parametrize(
    "custom_properties, expected",
    [
        ([{"property": "binary", "value": True}], "bytes"),
        (
            [{"property": "binary", "value": True}, {"property": "typeSize", "value": 16}],
            {"type": "fixed", "name": "users.digest", "size": 16},
        ),
    ],
    ids=["bytes", "fixed"],
)
def test_write_should_write_binary_string_as_bytes_or_fixed(custom_properties, expected):
    # Arrange
    schema = Schema(name="users").string(
        "digest",
        required=True,
        customProperties=custom_properties,
    )

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]["type"]
    assert actual == expected


def test_write_should_name_nested_record_by_full_path():
    # Arrange
    schema = (
        Schema(name="users")
        .object("address", required=True)
        .object("address.geo", required=True)
        .number("address.geo.lat", required=True)
    )

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]
    expected = {
        "name": "address",
        "type": {
            "type": "record",
            "name": "users.address",
            "fields": [
                {
                    "name": "geo",
                    "type": {
                        "type": "record",
                        "name": "users.address.geo",
                        "fields": [{"name": "lat", "type": "double"}],
                    },
                }
            ],
        },
    }
    assert actual == expected


@pytest.mark.parametrize(
    "required, expected",
    [
        (True, {"type": "array", "items": "string"}),
        (False, {"type": "array", "items": ["null", "string"]}),
    ],
)
def test_write_should_write_array_with_item_nullability(required, expected):
    # Arrange
    schema = Schema(
        name="users",
        properties=[
            Property(
                name="tags",
                logicalType="array",
                required=True,
                items=Property(logicalType="string", required=required),
            )
        ],
    )

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]["type"]
    assert actual == expected


def test_write_should_name_array_item_record_by_full_path():
    # Arrange
    schema = Schema(
        name="users",
        properties=[
            Property(
                name="friends",
                logicalType="array",
                required=True,
                items=Property(
                    logicalType="object",
                    required=True,
                    properties=[Property(name="name", logicalType="string", required=True)],
                ),
            )
        ],
    )

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]["type"]
    expected = {
        "type": "array",
        "items": {
            "type": "record",
            "name": "users.friends.items",
            "fields": [{"name": "name", "type": "string"}],
        },
    }
    assert actual == expected


def test_write_should_write_map_with_value_nullability():
    # Arrange
    schema = Schema(
        name="users",
        properties=[
            Property(
                name="scores",
                logicalType="map",
                required=True,
                map=Map(
                    key=Property(logicalType="string"),
                    value=Property(logicalType="integer", required=True),
                ),
            )
        ],
    )

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]["type"]
    expected = {"type": "map", "values": "long"}
    assert actual == expected


def test_write_should_write_string_with_enum_values_as_enum_named_by_full_path():
    # Arrange
    schema = Schema(name="users").string(
        "status",
        required=True,
        enum=[{"value": "ACTIVE"}, {"value": "INACTIVE"}],
    )

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]["type"]
    expected = {"type": "enum", "name": "users.status", "symbols": ["ACTIVE", "INACTIVE"]}
    assert actual == expected


@pytest.mark.parametrize(
    "schema, expected",
    [
        (
            Schema(name="t").integer(
                "id",
                required=True,
                primaryKey=True,
                classification="public",
                tags=["key"],
            ),
            {
                "name": "id",
                "type": "long",
                "odcs": {"tags": ["key"], "primaryKey": True, "classification": "public"},
            },
        ),
        (
            Schema(name="t").integer("id", required=False),
            {"name": "id", "type": ["null", "long"], "default": None, "odcs": {"required": False}},
        ),
    ],
    ids=["unknown_to_avro", "explicit_optional"],
)
def test_write_should_write_property_attributes_avro_cannot_express_under_odcs(schema, expected):
    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]
    assert actual == expected


def test_write_should_write_schema_attributes_avro_cannot_express_under_odcs():
    # Arrange
    schema = Schema(name="t", tags=["sales"]).integer("id", required=True)

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {
        "type": "record",
        "name": "t",
        "fields": [{"name": "id", "type": "long"}],
        "odcs": {"tags": ["sales"]},
    }
    assert actual == expected


@pytest.mark.parametrize(
    "prop, expected",
    [
        (
            Property(
                name="tags",
                logicalType="array",
                required=True,
                items=Property(logicalType="string", required=True, description="One tag"),
            ),
            {"items": {"description": "One tag"}},
        ),
        (
            Property(
                name="labels",
                logicalType="map",
                required=True,
                map=Map(
                    key=Property(logicalType="string", description="Label name"),
                    value=Property(logicalType="string", required=True, classification="pii"),
                ),
            ),
            {"map": {"key": {"description": "Label name"}, "value": {"classification": "pii"}}},
        ),
        (
            Property(
                name="labels",
                logicalType="map",
                required=True,
                map=Map(
                    key=Property(logicalType="string", required=True),
                    value=Property(logicalType="string", required=True),
                ),
            ),
            {"map": {"key": {"required": True}}},
        ),
        (
            Property(
                name="labels",
                logicalType="map",
                required=True,
                map=Map(value=Property(logicalType="string", required=True)),
            ),
            {"map": {"key": None}},
        ),
    ],
    ids=["array_items", "map_key_and_value", "map_key_required", "map_without_key"],
)
def test_write_should_write_nested_attributes_under_odcs_of_their_field(prop, expected):
    # Arrange
    schema = Schema(name="t", properties=[prop])

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]["odcs"]
    assert actual == expected


def test_write_should_name_nested_type_after_type_name_and_namespace():
    # Arrange
    schema = (
        Schema(name="users")
        .object(
            "home",
            required=True,
            customProperties=[
                {"property": "typeName", "value": "Address"},
                {"property": "namespace", "value": "com.acme.geo"},
            ],
        )
        .string("home.city", required=True)
    )

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]["type"]
    expected = {
        "type": "record",
        "name": "Address",
        "namespace": "com.acme.geo",
        "fields": [{"name": "city", "type": "string"}],
    }
    assert actual == expected


def test_write_should_write_schema_namespace_as_record_namespace():
    # Arrange
    schema = Schema(
        name="User",
        customProperties=[{"property": "namespace", "value": "com.acme"}],
    ).string("id", required=True)

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {
        "type": "record",
        "name": "User",
        "namespace": "com.acme",
        "fields": [{"name": "id", "type": "string"}],
    }
    assert actual == expected


@pytest.mark.parametrize(
    "schema, expected",
    [
        (
            Schema(name="users").integer(
                "age",
                required=True,
                logicalTypeOptions={"format": "i32"},
                customProperties=[{"property": "default", "value": 18}],
            ),
            {"name": "age", "type": "int", "default": 18},
        ),
        (
            Schema(name="users").integer(
                "id",
                required=True,
                customProperties=[{"property": "order", "value": "descending"}],
            ),
            {"name": "id", "type": "long", "order": "descending"},
        ),
        (
            Schema(name="users").string(
                "email",
                required=True,
                customProperties=[{"property": "pii", "value": True}],
            ),
            {"name": "email", "type": "string", "pii": True},
        ),
    ],
    ids=["default", "order", "other"],
)
def test_write_should_write_field_custom_properties_as_avro_attributes(schema, expected):
    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]
    assert actual == expected


def test_write_should_write_schema_custom_property_as_record_attribute():
    # Arrange
    schema = Schema(
        name="customer",
        customProperties=[{"property": "connect.name", "value": "com.acme.Customer"}],
    ).integer("id", required=True)

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {
        "type": "record",
        "name": "customer",
        "fields": [{"name": "id", "type": "long"}],
        "connect.name": "com.acme.Customer",
    }
    assert actual == expected


@pytest.mark.parametrize(
    "prop, expected",
    [
        (
            Property(
                name="field",
                logicalType="string",
                required=True,
                customProperties=[
                    {"property": "avro.java.string", "value": "String", "vendor": "avro"}
                ],
            ),
            {"type": "string", "avro.java.string": "String"},
        ),
        (
            Property(
                name="field",
                logicalType="string",
                customProperties=[
                    {"property": "avro.java.string", "value": "String", "vendor": "avro"}
                ],
            ),
            ["null", {"type": "string", "avro.java.string": "String"}],
        ),
        (
            Property(
                name="field",
                logicalType="array",
                required=True,
                items=Property(
                    logicalType="string",
                    required=True,
                    customProperties=[
                        {"property": "avro.java.string", "value": "String", "vendor": "avro"}
                    ],
                ),
            ),
            {"type": "array", "items": {"type": "string", "avro.java.string": "String"}},
        ),
        (
            Property(
                name="field",
                logicalType="map",
                required=True,
                map=Map(
                    key=Property(logicalType="string"),
                    value=Property(
                        logicalType="string",
                        required=True,
                        customProperties=[
                            {"property": "avro.java.string", "value": "String", "vendor": "avro"}
                        ],
                    ),
                ),
            ),
            {"type": "map", "values": {"type": "string", "avro.java.string": "String"}},
        ),
        (
            Property(
                name="field",
                logicalType="object",
                required=True,
                properties=[Property(name="city", logicalType="string", required=True)],
                customProperties=[
                    {"property": "connect.name", "value": "com.acme.Address", "vendor": "avro"}
                ],
            ),
            {
                "type": "record",
                "name": "users.field",
                "fields": [{"name": "city", "type": "string"}],
                "connect.name": "com.acme.Address",
            },
        ),
    ],
    ids=["primitive", "nullable", "array_items", "map_values", "nested_record"],
)
def test_write_should_write_avro_vendor_custom_property_as_type_attribute(prop, expected):
    # Arrange
    schema = Schema(name="users", properties=[prop])

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]["type"]
    assert actual == expected


def test_write_should_write_unknown_logical_type_back_on_type():
    # Arrange
    schema = Schema(name="users").integer(
        "nanos",
        required=True,
        physicalType="long",
        customProperties=[{"property": "logicalType", "value": "iso-8601", "vendor": "avro"}],
    )

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]
    expected = {"name": "nanos", "type": {"type": "long", "logicalType": "iso-8601"}}
    assert actual == expected


def test_write_should_not_take_avro_vendor_default_as_field_default():
    # Arrange
    schema = Schema(name="users").string(
        "status",
        enum=[{"value": "ACTIVE"}, {"value": "INACTIVE"}],
        customProperties=[{"property": "default", "value": "ACTIVE", "vendor": "avro"}],
    )

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]
    expected = {
        "name": "status",
        "type": [
            "null",
            {
                "type": "enum",
                "name": "users.status",
                "symbols": ["ACTIVE", "INACTIVE"],
                "default": "ACTIVE",
            },
        ],
        "default": None,
    }
    assert actual == expected


def test_write_should_put_type_first_in_union_when_optional_property_has_default():
    # Arrange
    schema = Schema(name="users").string(
        "nick",
        customProperties=[{"property": "default", "value": "anon"}],
    )

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]
    expected = {"name": "nick", "type": ["string", "null"], "default": "anon"}
    assert actual == expected


def test_write_should_write_avro_synonyms_as_aliases():
    # Arrange
    schema = Schema(
        name="users",
        synonyms=[{"synonym": "people", "source": "avro"}],
    ).string("email", required=True, synonyms=[{"synonym": "mail", "source": "avro"}])

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "email", "type": "string", "aliases": ["mail"]}],
        "aliases": ["people"],
    }
    assert actual == expected


@pytest.mark.parametrize(
    "schema, expected",
    [
        (
            Schema(name="users").string(
                "email",
                required=True,
                synonyms=[{"synonym": "client e-mail"}, {"synonym": "mail", "source": "avro"}],
            ),
            {
                "name": "email",
                "type": "string",
                "aliases": ["mail"],
                "odcs": {"synonyms": [{"synonym": "client e-mail"}]},
            },
        ),
        (
            Schema(name="users").integer(
                "age",
                required=True,
                customProperties=[
                    {"property": "owner", "value": "sales", "description": "Owning team"},
                    {"property": "default", "value": 7},
                ],
            ),
            {
                "name": "age",
                "type": "long",
                "default": 7,
                "odcs": {
                    "customProperties": [
                        {"property": "owner", "value": "sales", "description": "Owning team"}
                    ]
                },
            },
        ),
        (
            Schema(name="users").integer(
                "age",
                required=True,
                customProperties=[{"id": "owner_id", "property": "owner", "value": "sales"}],
            ),
            {
                "name": "age",
                "type": "long",
                "odcs": {
                    "customProperties": [{"id": "owner_id", "property": "owner", "value": "sales"}]
                },
            },
        ),
    ],
    ids=["other_synonyms", "custom_property_with_description", "custom_property_with_id"],
)
def test_write_should_write_other_synonyms_and_custom_properties_under_odcs(schema, expected):
    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]
    assert actual == expected


@pytest.mark.parametrize(
    "custom_property, expected",
    [
        (
            {"property": "type", "value": "x"},
            {
                "name": "email",
                "type": "string",
                "odcs": {"customProperties": [{"property": "type", "value": "x"}]},
            },
        ),
        (
            {"property": "name", "value": "x"},
            {
                "name": "email",
                "type": "string",
                "odcs": {"customProperties": [{"property": "name", "value": "x"}]},
            },
        ),
        (
            {"property": "doc", "value": "x"},
            {
                "name": "email",
                "type": "string",
                "odcs": {"customProperties": [{"property": "doc", "value": "x"}]},
            },
        ),
        (
            {"property": "type", "value": "x", "vendor": "avro"},
            {
                "name": "email",
                "type": "string",
                "odcs": {
                    "customProperties": [{"property": "type", "value": "x", "vendor": "avro"}]
                },
            },
        ),
    ],
    ids=["type", "name", "doc", "avro_type"],
)
def test_write_should_write_custom_property_with_reserved_name_under_odcs(
    custom_property, expected
):
    # Arrange
    schema = Schema(name="users").string(
        "email",
        required=True,
        customProperties=[custom_property],
    )

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]
    assert actual == expected


def test_write_should_write_type_name_and_namespace_under_odcs_when_property_is_not_named_type():
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
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]
    expected = {
        "name": "email",
        "type": "string",
        "odcs": {
            "customProperties": [
                {"property": "typeName", "value": "Email"},
                {"property": "namespace", "value": "com.acme"},
            ]
        },
    }
    assert actual == expected


def test_write_should_preserve_schema_name_when_schema_has_type_name():
    # Arrange
    schema = Schema(
        name="users",
        customProperties=[
            {"property": "typeName", "value": "Other"},
            {"property": "namespace", "value": "com.acme"},
        ],
    ).string("email", required=True)

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {
        "type": "record",
        "name": "users",
        "namespace": "com.acme",
        "fields": [{"name": "email", "type": "string"}],
        "odcs": {"customProperties": [{"property": "typeName", "value": "Other"}]},
    }
    assert actual == expected


def test_write_should_write_schema_default_and_order_under_odcs():
    # Arrange
    schema = Schema(
        name="users",
        customProperties=[
            {"property": "default", "value": 1},
            {"property": "order", "value": "ascending"},
        ],
    ).string("email", required=True)

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "email", "type": "string"}],
        "odcs": {
            "customProperties": [
                {"property": "default", "value": 1},
                {"property": "order", "value": "ascending"},
            ]
        },
    }
    assert actual == expected


@pytest.mark.parametrize(
    "prop, expected",
    [
        (
            Property(
                name="tags",
                logicalType="array",
                required=True,
                items=Property(
                    logicalType="string",
                    customProperties=[
                        {"property": "default", "value": "none"},
                        {"property": "order", "value": "descending"},
                    ],
                ),
            ),
            {
                "name": "tags",
                "type": {"type": "array", "items": ["null", "string"]},
                "odcs": {
                    "items": {
                        "customProperties": [
                            {"property": "default", "value": "none"},
                            {"property": "order", "value": "descending"},
                        ]
                    }
                },
            },
        ),
        (
            Property(
                name="labels",
                logicalType="map",
                required=True,
                map=Map(
                    key=Property(logicalType="string"),
                    value=Property(
                        logicalType="string",
                        customProperties=[{"property": "default", "value": "none"}],
                    ),
                ),
            ),
            {
                "name": "labels",
                "type": {"type": "map", "values": ["null", "string"]},
                "odcs": {
                    "map": {
                        "value": {"customProperties": [{"property": "default", "value": "none"}]}
                    }
                },
            },
        ),
    ],
    ids=["array_items", "map_values"],
)
def test_write_should_write_default_under_odcs_with_null_first_when_element_is_not_field(
    prop, expected
):
    # Arrange
    schema = Schema(name="users", properties=[prop])

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]
    assert actual == expected


def test_write_should_refer_to_repeated_type_by_name():
    # Arrange
    schema = (
        Schema(name="users")
        .object(
            "home", required=True, customProperties=[{"property": "typeName", "value": "Address"}]
        )
        .string("home.city", required=True)
        .object(
            "work", required=True, customProperties=[{"property": "typeName", "value": "Address"}]
        )
        .string("work.city", required=True)
    )

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"]
    expected = [
        {
            "name": "home",
            "type": {
                "type": "record",
                "name": "Address",
                "fields": [{"name": "city", "type": "string"}],
            },
        },
        {"name": "work", "type": "Address"},
    ]
    assert actual == expected


@pytest.mark.parametrize(
    "prop, expected",
    [
        (
            Property(
                name="price",
                logicalType="number",
                physicalType="bytes",
                required=True,
                customProperties=[
                    {"property": "precision", "value": 10},
                    {"property": "scale", "value": 2},
                ],
            ),
            {
                "name": "price",
                "type": {"type": "bytes", "logicalType": "decimal", "precision": 10, "scale": 2},
            },
        ),
        (
            Property(
                name="price",
                logicalType="number",
                required=True,
                customProperties=[{"property": "precision", "value": 10}],
            ),
            {
                "name": "price",
                "type": {"type": "bytes", "logicalType": "decimal", "precision": 10},
            },
        ),
        (
            Property(
                name="price",
                logicalType="number",
                required=True,
                customProperties=[
                    {"property": "precision", "value": 10},
                    {"property": "scale", "value": 2},
                    {"property": "typeSize", "value": 8},
                ],
            ),
            {
                "name": "price",
                "type": {
                    "type": "fixed",
                    "name": "users.price",
                    "size": 8,
                    "logicalType": "decimal",
                    "precision": 10,
                    "scale": 2,
                },
            },
        ),
        (
            Property(
                name="price",
                logicalType="number",
                physicalType="fixed",
                required=True,
                customProperties=[{"property": "precision", "value": 10}],
            ),
            {
                "name": "price",
                "type": {"type": "bytes", "logicalType": "decimal", "precision": 10},
            },
        ),
    ],
    ids=["on_bytes", "without_physical_type", "on_fixed", "physical_fixed_without_type_size"],
)
def test_write_should_write_decimal_from_precision_and_scale(prop, expected):
    # Arrange
    schema = Schema(name="users", properties=[prop])

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]
    assert actual == expected


@pytest.mark.parametrize(
    "prop, expected",
    [
        (
            Property(name="at", logicalType="timestamp", required=True),
            {"type": "long", "logicalType": "timestamp-micros"},
        ),
        (
            Property(
                name="at",
                logicalType="timestamp",
                required=True,
                customProperties=[{"property": "timeUnit", "value": "millis"}],
            ),
            {"type": "long", "logicalType": "timestamp-millis"},
        ),
        (
            Property(
                name="at",
                logicalType="timestamp",
                required=True,
                logicalTypeOptions={"timezone": False},
            ),
            {"type": "long", "logicalType": "local-timestamp-micros"},
        ),
        (
            Property(
                name="at",
                logicalType="timestamp",
                required=True,
                logicalTypeOptions={"timezone": False},
                customProperties=[{"property": "timeUnit", "value": "nanos"}],
            ),
            {"type": "long", "logicalType": "local-timestamp-nanos"},
        ),
        (
            Property(
                name="at",
                logicalType="time",
                required=True,
                customProperties=[{"property": "timeUnit", "value": "millis"}],
            ),
            {"type": "int", "logicalType": "time-millis"},
        ),
        (
            Property(name="at", logicalType="timestamp", physicalType="long", required=True),
            {"type": "long", "logicalType": "timestamp-micros"},
        ),
    ],
    ids=[
        "timestamp_default",
        "timestamp_millis",
        "local_timestamp",
        "local_timestamp_nanos",
        "time_millis",
        "timestamp_on_long",
    ],
)
def test_write_should_write_temporal_type_from_time_unit_and_timezone(prop, expected):
    # Arrange
    schema = Schema(name="users", properties=[prop])

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]["type"]
    assert actual == expected


def test_write_should_write_uuid_from_format():
    # Arrange
    schema = Schema(name="users").string(
        "id",
        required=True,
        logicalTypeOptions={"format": "uuid"},
    )

    # Act
    result = AvroSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]
    expected = {"name": "id", "type": {"type": "string", "logicalType": "uuid"}}
    assert actual == expected


def test_write_should_raise_schema_error_when_map_lacks_value():
    # Arrange
    schema = Schema(
        name="users",
        properties=[
            Property(
                name="scores",
                logicalType="map",
                map=Map(key=Property(logicalType="string")),
            )
        ],
    )

    # Act / Assert
    with pytest.raises(SchemaError, match="Map property `scores` needs a value definition"):
        AvroSchemaWriter().write(schema)


@pytest.mark.parametrize(
    "prop",
    [
        Property(name="field"),
        Property(name="field", logicalType="vector"),
    ],
)
def test_write_should_raise_schema_error_when_property_has_no_avro_type(prop):
    # Arrange
    schema = Schema(name="users", properties=[prop])

    # Act / Assert
    with pytest.raises(SchemaError, match="Property `field` has no type Avro can represent"):
        AvroSchemaWriter().write(schema)


@pytest.mark.parametrize(
    "name",
    [
        "first name",
        "1st",
    ],
)
def test_write_should_raise_schema_error_when_property_name_is_not_avro_name(name):
    # Arrange
    schema = Schema(name="users").string(name, required=True)

    # Act / Assert
    with pytest.raises(SchemaError, match=f"Property `{name}` is not a valid Avro name"):
        AvroSchemaWriter().write(schema)


@pytest.mark.parametrize(
    "name",
    [
        "my table",
        "1st",
    ],
)
def test_write_should_raise_schema_error_when_schema_name_is_not_avro_name(name):
    # Arrange
    schema = Schema(name=name).string("id", required=True)

    # Act / Assert
    with pytest.raises(SchemaError, match=f"Schema `{name}` is not a valid Avro name"):
        AvroSchemaWriter().write(schema)


def test_write_should_raise_schema_error_when_map_key_is_not_string():
    # Arrange
    schema = Schema(name="t").map("m", value="string", key="integer")

    # Act / Assert
    with pytest.raises(SchemaError, match="Map property `m` needs a string key for Avro"):
        AvroSchemaWriter().write(schema)


@pytest.mark.parametrize(
    "value",
    [
        "pt-BR",
        1,
    ],
)
def test_write_should_raise_schema_error_when_enum_value_is_not_avro_name(value):
    # Arrange
    schema = Schema(name="users").string("locale", required=True, enum=[{"value": value}])

    # Act / Assert
    with pytest.raises(SchemaError, match="Enum values of `locale` are not valid Avro names"):
        AvroSchemaWriter().write(schema)


def test_write_should_raise_schema_error_when_non_string_property_has_enum_values():
    # Arrange
    schema = Schema(name="t").integer("n", enum=[{"value": 1}])

    # Act / Assert
    with pytest.raises(
        SchemaError, match="Property `n` has enum values, but Avro enums only hold strings"
    ):
        AvroSchemaWriter().write(schema)


def test_write_should_raise_schema_error_when_type_name_is_not_avro_name():
    # Arrange
    schema = (
        Schema(name="users")
        .object("home", customProperties=[{"property": "typeName", "value": "not ok"}])
        .string("home.city")
    )

    # Act / Assert
    with pytest.raises(SchemaError, match="Type `not ok` is not a valid Avro name"):
        AvroSchemaWriter().write(schema)


def test_write_should_raise_schema_error_when_types_with_same_name_differ():
    # Arrange
    schema = (
        Schema(name="users")
        .object("home", customProperties=[{"property": "typeName", "value": "Address"}])
        .string("home.city")
        .object("work", customProperties=[{"property": "typeName", "value": "Address"}])
        .string("work.street")
    )

    # Act / Assert
    with pytest.raises(SchemaError, match="Avro types named `Address` have different definitions"):
        AvroSchemaWriter().write(schema)


def test_write_should_raise_schema_error_when_avro_has_no_type_for_format():
    # Arrange
    schema = Schema(name="users").integer(
        "id",
        required=True,
        logicalTypeOptions={"format": "i128"},
    )

    # Act / Assert
    with pytest.raises(SchemaError, match="Property `id` has no Avro type for format `i128`"):
        AvroSchemaWriter().write(schema)


def test_write_should_raise_schema_error_when_avro_has_no_type_for_time_unit():
    # Arrange
    schema = Schema(name="users").time(
        "at",
        required=True,
        customProperties=[{"property": "timeUnit", "value": "nanos"}],
    )

    # Act / Assert
    with pytest.raises(SchemaError, match="Property `at` has no Avro type for a time in nanos"):
        AvroSchemaWriter().write(schema)
