import pytest

from tiozin.api.metadata.schema.converters.avro import AvroSchemaReader
from tiozin.exceptions import SchemaError


def test_read_should_read_record_field_as_required_property():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "id", "type": "long"}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

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
    "avro_type, expected_physical_type",
    [
        (["null", "long"], '["null", "long"]'),
        (["long", "null"], '["long", "null"]'),
    ],
)
def test_read_should_leave_required_unset_when_type_is_null_union(
    avro_type, expected_physical_type
):
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "id", "type": avro_type, "default": None}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "users",
        "properties": [
            {
                "name": "id",
                "logicalType": "integer",
                "physicalType": expected_physical_type,
                "logicalTypeOptions": {"format": "i64"},
            }
        ],
    }
    assert actual == expected


def test_read_should_read_plain_type_as_required():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "email", "type": "string"}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "users",
        "properties": [
            {
                "name": "email",
                "logicalType": "string",
                "physicalType": "string",
                "required": True,
            }
        ],
    }
    assert actual == expected


def test_read_should_read_single_type_union_as_required():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "email", "type": ["string"]}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "users",
        "properties": [
            {
                "name": "email",
                "logicalType": "string",
                "physicalType": '["string"]',
                "required": True,
            }
        ],
    }
    assert actual == expected


@pytest.mark.parametrize(
    "field",
    [
        {"name": "email", "type": ["null", "string"]},
        {"name": "email", "type": ["null", "string"], "default": None},
    ],
    ids=["without_default", "with_null_default"],
)
def test_read_should_not_read_null_default_of_null_union(field):
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [field],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "users",
        "properties": [
            {"name": "email", "logicalType": "string", "physicalType": '["null", "string"]'}
        ],
    }
    assert actual == expected


def test_read_should_read_non_null_default_of_null_union_as_custom_property():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "country", "type": ["string", "null"], "default": "BR"}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "users",
        "properties": [
            {
                "name": "country",
                "logicalType": "string",
                "physicalType": '["string", "null"]',
                "customProperties": [{"property": "default", "value": "BR"}],
            }
        ],
    }
    assert actual == expected


def test_read_should_read_field_doc_as_description():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "name", "type": "string", "doc": "Full name"}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result["name"].description
    expected = "Full name"
    assert actual == expected


def test_read_should_read_record_doc_as_description():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "doc": "Registered users",
        "fields": [{"name": "name", "type": "string"}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result.description
    expected = "Registered users"
    assert actual == expected


@pytest.mark.parametrize(
    "avro_type, expected",
    [
        ("string", ("string", "string")),
        ("bytes", ("string", "bytes")),
        ("boolean", ("boolean", "boolean")),
        ("int", ("integer", "int")),
        ("long", ("integer", "long")),
        ("float", ("number", "float")),
        ("double", ("number", "double")),
        ({"type": "long"}, ("integer", '{"type": "long"}')),
        (
            {"type": "string", "logicalType": "uuid"},
            ("string", '{"type": "string", "logicalType": "uuid"}'),
        ),
        (
            {"type": "int", "logicalType": "date"},
            ("date", '{"type": "int", "logicalType": "date"}'),
        ),
        (
            {"type": "int", "logicalType": "time-millis"},
            ("time", '{"type": "int", "logicalType": "time-millis"}'),
        ),
        (
            {"type": "long", "logicalType": "time-micros"},
            ("time", '{"type": "long", "logicalType": "time-micros"}'),
        ),
        (
            {"type": "long", "logicalType": "timestamp-millis"},
            ("timestamp", '{"type": "long", "logicalType": "timestamp-millis"}'),
        ),
        (
            {"type": "long", "logicalType": "timestamp-micros"},
            ("timestamp", '{"type": "long", "logicalType": "timestamp-micros"}'),
        ),
        (
            {"type": "long", "logicalType": "local-timestamp-millis"},
            ("timestamp", '{"type": "long", "logicalType": "local-timestamp-millis"}'),
        ),
    ],
)
def test_read_should_map_avro_type_to_logical_and_physical_type(avro_type, expected):
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "field", "type": avro_type}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = (
        result["field"].logicalType,
        result["field"].physicalType,
    )
    assert actual == expected


@pytest.mark.parametrize(
    "avro_type, expected",
    [
        ("int", {"format": "i32"}),
        ("long", {"format": "i64"}),
        ("float", {"format": "f32"}),
        ("double", {"format": "f64"}),
    ],
)
def test_read_should_read_size_as_format(avro_type, expected):
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "field", "type": avro_type}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result["field"].model_dump(exclude_unset=True)["logicalTypeOptions"]
    assert actual == expected


def test_read_should_read_bytes_as_binary_string():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "payload", "type": "bytes"}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result["payload"].model_dump(exclude_unset=True)
    expected = {
        "name": "payload",
        "logicalType": "string",
        "physicalType": "bytes",
        "required": True,
        "customProperties": [{"property": "binary", "value": True}],
    }
    assert actual == expected


def test_read_should_read_fixed_as_binary_string_with_type_size():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "hash", "type": {"type": "fixed", "name": "Hash", "size": 16}}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result["hash"].model_dump(exclude_unset=True)
    expected = {
        "name": "hash",
        "logicalType": "string",
        "physicalType": '{"type": "fixed", "name": "Hash", "size": 16}',
        "required": True,
        "customProperties": [
            {"property": "typeName", "value": "Hash"},
            {"property": "binary", "value": True},
            {"property": "typeSize", "value": 16},
        ],
    }
    assert actual == expected


@pytest.mark.parametrize(
    "avro_type, expected_physical_type, expected_custom_properties",
    [
        (
            {"type": "bytes", "logicalType": "decimal", "precision": 10, "scale": 2},
            '{"type": "bytes", "logicalType": "decimal", "precision": 10, "scale": 2}',
            [{"property": "precision", "value": 10}, {"property": "scale", "value": 2}],
        ),
        (
            {"type": "bytes", "logicalType": "decimal", "precision": 10},
            '{"type": "bytes", "logicalType": "decimal", "precision": 10}',
            [{"property": "precision", "value": 10}],
        ),
    ],
)
def test_read_should_read_decimal_as_number_with_precision_and_scale(
    avro_type, expected_physical_type, expected_custom_properties
):
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "balance", "type": avro_type}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result["balance"].model_dump(exclude_unset=True)
    expected = {
        "name": "balance",
        "logicalType": "number",
        "physicalType": expected_physical_type,
        "required": True,
        "customProperties": expected_custom_properties,
    }
    assert actual == expected


def test_read_should_read_decimal_on_fixed_with_type_size():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [
            {
                "name": "balance",
                "type": {
                    "type": "fixed",
                    "name": "users.balance",
                    "size": 8,
                    "logicalType": "decimal",
                    "precision": 10,
                    "scale": 2,
                },
            }
        ],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result["balance"].model_dump(exclude_unset=True)
    expected = {
        "name": "balance",
        "logicalType": "number",
        "physicalType": (
            '{"type": "fixed", "name": "users.balance", "size": 8, '
            '"logicalType": "decimal", "precision": 10, "scale": 2}'
        ),
        "required": True,
        "customProperties": [
            {"property": "precision", "value": 10},
            {"property": "scale", "value": 2},
            {"property": "typeSize", "value": 8},
        ],
    }
    assert actual == expected


@pytest.mark.parametrize(
    "avro_type, expected",
    [
        (
            {"type": "int", "logicalType": "time-millis"},
            {
                "name": "at",
                "logicalType": "time",
                "physicalType": '{"type": "int", "logicalType": "time-millis"}',
                "required": True,
                "customProperties": [{"property": "timeUnit", "value": "millis"}],
            },
        ),
        (
            {"type": "long", "logicalType": "timestamp-nanos"},
            {
                "name": "at",
                "logicalType": "timestamp",
                "physicalType": '{"type": "long", "logicalType": "timestamp-nanos"}',
                "required": True,
                "customProperties": [{"property": "timeUnit", "value": "nanos"}],
                "logicalTypeOptions": {"timezone": True},
            },
        ),
        (
            {"type": "long", "logicalType": "local-timestamp-micros"},
            {
                "name": "at",
                "logicalType": "timestamp",
                "physicalType": '{"type": "long", "logicalType": "local-timestamp-micros"}',
                "required": True,
                "customProperties": [{"property": "timeUnit", "value": "micros"}],
                "logicalTypeOptions": {"timezone": False},
            },
        ),
    ],
    ids=["time_millis", "timestamp_nanos", "local_timestamp_micros"],
)
def test_read_should_read_time_unit_and_timezone_of_temporal_type(avro_type, expected):
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "at", "type": avro_type}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result["at"].model_dump(exclude_unset=True)
    assert actual == expected


def test_read_should_read_uuid_as_string_with_uuid_format():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "id", "type": {"type": "string", "logicalType": "uuid"}}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result["id"].model_dump(exclude_unset=True)
    expected = {
        "name": "id",
        "logicalType": "string",
        "physicalType": '{"type": "string", "logicalType": "uuid"}',
        "required": True,
        "logicalTypeOptions": {"format": "uuid"},
    }
    assert actual == expected


def test_read_should_read_enum_as_string_with_enum_values():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [
            {
                "name": "status",
                "type": {"type": "enum", "name": "users.status", "symbols": ["A", "B"]},
            }
        ],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result["status"].model_dump(exclude_unset=True)
    expected = {
        "name": "status",
        "logicalType": "string",
        "physicalType": '{"type": "enum", "name": "users.status", "symbols": ["A", "B"]}',
        "enum": [{"value": "A"}, {"value": "B"}],
        "required": True,
    }
    assert actual == expected


def test_read_should_read_nested_record_as_object():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [
            {
                "name": "address",
                "type": {
                    "type": "record",
                    "name": "users.address",
                    "fields": [{"name": "city", "type": "string"}],
                },
            }
        ],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "users",
        "properties": [
            {
                "name": "address",
                "logicalType": "object",
                "physicalType": (
                    '{"type": "record", "name": "users.address", '
                    '"fields": [{"name": "city", "type": "string"}]}'
                ),
                "required": True,
                "properties": [
                    {
                        "name": "city",
                        "logicalType": "string",
                        "physicalType": "string",
                        "required": True,
                    }
                ],
            }
        ],
    }
    assert actual == expected


@pytest.mark.parametrize(
    "avro_type, expected",
    [
        (
            {
                "type": "array",
                "items": {
                    "type": "record",
                    "name": "users.places.items",
                    "fields": [{"name": "city", "type": "string"}],
                },
            },
            {
                "name": "places",
                "logicalType": "array",
                "physicalType": (
                    '{"type": "array", "items": {"type": "record", "name": "users.places.items", '
                    '"fields": [{"name": "city", "type": "string"}]}}'
                ),
                "required": True,
                "items": {
                    "logicalType": "object",
                    "physicalType": (
                        '{"type": "record", "name": "users.places.items", '
                        '"fields": [{"name": "city", "type": "string"}]}'
                    ),
                    "required": True,
                    "properties": [
                        {
                            "name": "city",
                            "logicalType": "string",
                            "physicalType": "string",
                            "required": True,
                        }
                    ],
                },
            },
        ),
        (
            {
                "type": "map",
                "values": {
                    "type": "record",
                    "name": "users.places.values",
                    "fields": [{"name": "city", "type": "string"}],
                },
            },
            {
                "name": "places",
                "logicalType": "map",
                "physicalType": (
                    '{"type": "map", "values": {"type": "record", "name": "users.places.values", '
                    '"fields": [{"name": "city", "type": "string"}]}}'
                ),
                "required": True,
                "map": {
                    "key": {"logicalType": "string", "physicalType": "string"},
                    "value": {
                        "logicalType": "object",
                        "physicalType": (
                            '{"type": "record", "name": "users.places.values", '
                            '"fields": [{"name": "city", "type": "string"}]}'
                        ),
                        "required": True,
                        "properties": [
                            {
                                "name": "city",
                                "logicalType": "string",
                                "physicalType": "string",
                                "required": True,
                            }
                        ],
                    },
                },
            },
        ),
    ],
    ids=["array_items", "map_values"],
)
def test_read_should_not_read_path_name_of_items_and_values_as_type_name(avro_type, expected):
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "places", "type": avro_type}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result["places"].model_dump(exclude_unset=True)
    assert actual == expected


def test_read_should_keep_record_name_root_when_odcs_does_not_unset_it():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "root",
        "fields": [{"name": "id", "type": "long"}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "root",
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


def test_read_should_read_array_with_item_nullability():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "tags", "type": {"type": "array", "items": ["null", "string"]}}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "users",
        "properties": [
            {
                "name": "tags",
                "logicalType": "array",
                "physicalType": '{"type": "array", "items": ["null", "string"]}',
                "required": True,
                "items": {"logicalType": "string", "physicalType": '["null", "string"]'},
            }
        ],
    }
    assert actual == expected


def test_read_should_read_map_with_string_keys():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "scores", "type": {"type": "map", "values": "long"}}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "users",
        "properties": [
            {
                "name": "scores",
                "logicalType": "map",
                "physicalType": '{"type": "map", "values": "long"}',
                "required": True,
                "map": {
                    "key": {"logicalType": "string", "physicalType": "string"},
                    "value": {
                        "logicalType": "integer",
                        "physicalType": "long",
                        "logicalTypeOptions": {"format": "i64"},
                        "required": True,
                    },
                },
            }
        ],
    }
    assert actual == expected


def test_read_should_apply_odcs_attributes_to_property():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "id", "type": "long", "odcs": {"primaryKey": True}}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result["id"].model_dump(exclude_unset=True)
    expected = {
        "name": "id",
        "logicalType": "integer",
        "physicalType": "long",
        "logicalTypeOptions": {"format": "i64"},
        "required": True,
        "primaryKey": True,
    }
    assert actual == expected


def test_read_should_apply_odcs_attributes_to_schema():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "id", "type": "long"}],
        "odcs": {"tags": ["sales"]},
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "users",
        "tags": ["sales"],
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


def test_read_should_prefer_odcs_attributes_over_avro_type():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "id", "type": "long", "odcs": {"physicalType": "bigint"}}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result["id"].physicalType
    expected = "bigint"
    assert actual == expected


def test_read_should_preserve_avro_value_when_odcs_value_is_null():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "id", "type": "long", "odcs": {"physicalType": None}}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result["id"].physicalType
    expected = "long"
    assert actual == expected


def test_read_should_apply_nested_odcs_attributes_to_items_and_map_entries():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [
            {
                "name": "tags",
                "type": {"type": "array", "items": "string"},
                "odcs": {"items": {"description": "One tag"}},
            },
            {
                "name": "labels",
                "type": {"type": "map", "values": "string"},
                "odcs": {
                    "map": {
                        "key": {"description": "Label name"},
                        "value": {"classification": "pii"},
                    }
                },
            },
        ],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "users",
        "properties": [
            {
                "name": "tags",
                "logicalType": "array",
                "physicalType": '{"type": "array", "items": "string"}',
                "required": True,
                "items": {
                    "logicalType": "string",
                    "physicalType": "string",
                    "required": True,
                    "description": "One tag",
                },
            },
            {
                "name": "labels",
                "logicalType": "map",
                "physicalType": '{"type": "map", "values": "string"}',
                "required": True,
                "map": {
                    "key": {
                        "logicalType": "string",
                        "physicalType": "string",
                        "description": "Label name",
                    },
                    "value": {
                        "logicalType": "string",
                        "physicalType": "string",
                        "required": True,
                        "classification": "pii",
                    },
                },
            },
        ],
    }
    assert actual == expected


def test_read_should_read_reference_as_type_it_refers_to():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [
            {"name": "status", "type": {"type": "enum", "name": "Status", "symbols": ["A"]}},
            {"name": "old_status", "type": "Status"},
        ],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result["old_status"].model_dump(exclude_unset=True)
    expected = {
        "name": "old_status",
        "logicalType": "string",
        "physicalType": "Status",
        "required": True,
        "enum": [{"value": "A"}],
        "customProperties": [{"property": "typeName", "value": "Status"}],
    }
    assert actual == expected


def test_read_should_read_field_default_as_custom_property():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "age", "type": "int", "default": 18}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result["age"].model_dump(exclude_unset=True)
    expected = {
        "name": "age",
        "logicalType": "integer",
        "physicalType": "int",
        "logicalTypeOptions": {"format": "i32"},
        "required": True,
        "customProperties": [{"property": "default", "value": 18}],
    }
    assert actual == expected


def test_read_should_read_field_order_as_custom_property():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "id", "type": "long", "order": "descending"}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result["id"].model_dump(exclude_unset=True)
    expected = {
        "name": "id",
        "logicalType": "integer",
        "physicalType": "long",
        "logicalTypeOptions": {"format": "i64"},
        "required": True,
        "customProperties": [{"property": "order", "value": "descending"}],
    }
    assert actual == expected


def test_read_should_read_namespaces_as_custom_properties():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "User",
        "namespace": "com.acme",
        "fields": [
            {
                "name": "home",
                "type": {
                    "type": "record",
                    "name": "Address",
                    "namespace": "com.acme.geo",
                    "fields": [{"name": "city", "type": "string"}],
                },
            }
        ],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "User",
        "customProperties": [{"property": "namespace", "value": "com.acme"}],
        "properties": [
            {
                "name": "home",
                "logicalType": "object",
                "physicalType": (
                    '{"type": "record", "name": "Address", "namespace": "com.acme.geo", '
                    '"fields": [{"name": "city", "type": "string"}]}'
                ),
                "required": True,
                "customProperties": [
                    {"property": "typeName", "value": "Address"},
                    {"property": "namespace", "value": "com.acme.geo"},
                ],
                "properties": [
                    {
                        "name": "city",
                        "logicalType": "string",
                        "physicalType": "string",
                        "required": True,
                    }
                ],
            }
        ],
    }
    assert actual == expected


def test_read_should_read_type_name_of_array_items():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [
            {
                "name": "places",
                "type": {
                    "type": "array",
                    "items": {
                        "type": "record",
                        "name": "Place",
                        "fields": [{"name": "city", "type": "string"}],
                    },
                },
            }
        ],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result["places"].items.model_dump(exclude_unset=True)
    expected = {
        "logicalType": "object",
        "physicalType": (
            '{"type": "record", "name": "Place", "fields": [{"name": "city", "type": "string"}]}'
        ),
        "required": True,
        "customProperties": [{"property": "typeName", "value": "Place"}],
        "properties": [
            {"name": "city", "logicalType": "string", "physicalType": "string", "required": True}
        ],
    }
    assert actual == expected


def test_read_should_read_aliases_as_avro_synonyms():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "aliases": ["people"],
        "fields": [{"name": "id", "type": "long", "aliases": ["user_id"]}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "users",
        "synonyms": [{"synonym": "people", "source": "avro"}],
        "properties": [
            {
                "name": "id",
                "logicalType": "integer",
                "physicalType": "long",
                "logicalTypeOptions": {"format": "i64"},
                "required": True,
                "synonyms": [{"synonym": "user_id", "source": "avro"}],
            }
        ],
    }
    assert actual == expected


def test_read_should_read_field_extra_attribute_as_custom_property():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "email", "type": "string", "pii": True}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result["email"].model_dump(exclude_unset=True)
    expected = {
        "name": "email",
        "logicalType": "string",
        "physicalType": "string",
        "required": True,
        "customProperties": [{"property": "pii", "value": True}],
    }
    assert actual == expected


@pytest.mark.parametrize(
    "avro_type, expected",
    [
        (
            {"type": "string", "avro.java.string": "String"},
            {
                "name": "field",
                "logicalType": "string",
                "physicalType": '{"type": "string", "avro.java.string": "String"}',
                "required": True,
                "customProperties": [
                    {"property": "avro.java.string", "value": "String", "vendor": "avro"}
                ],
            },
        ),
        (
            ["null", {"type": "string", "avro.java.string": "String"}],
            {
                "name": "field",
                "logicalType": "string",
                "physicalType": '["null", {"type": "string", "avro.java.string": "String"}]',
                "customProperties": [
                    {"property": "avro.java.string", "value": "String", "vendor": "avro"}
                ],
            },
        ),
        (
            {"type": "array", "items": {"type": "string", "avro.java.string": "String"}},
            {
                "name": "field",
                "logicalType": "array",
                "physicalType": (
                    '{"type": "array", "items": {"type": "string", "avro.java.string": "String"}}'
                ),
                "required": True,
                "items": {
                    "logicalType": "string",
                    "physicalType": '{"type": "string", "avro.java.string": "String"}',
                    "required": True,
                    "customProperties": [
                        {"property": "avro.java.string", "value": "String", "vendor": "avro"}
                    ],
                },
            },
        ),
        (
            {"type": "map", "values": {"type": "string", "avro.java.string": "String"}},
            {
                "name": "field",
                "logicalType": "map",
                "physicalType": (
                    '{"type": "map", "values": {"type": "string", "avro.java.string": "String"}}'
                ),
                "required": True,
                "map": {
                    "key": {"logicalType": "string", "physicalType": "string"},
                    "value": {
                        "logicalType": "string",
                        "physicalType": '{"type": "string", "avro.java.string": "String"}',
                        "required": True,
                        "customProperties": [
                            {"property": "avro.java.string", "value": "String", "vendor": "avro"}
                        ],
                    },
                },
            },
        ),
        (
            {
                "type": "record",
                "name": "Address",
                "fields": [{"name": "city", "type": "string"}],
                "connect.name": "com.acme.Address",
            },
            {
                "name": "field",
                "logicalType": "object",
                "physicalType": (
                    '{"type": "record", "name": "Address", '
                    '"fields": [{"name": "city", "type": "string"}], '
                    '"connect.name": "com.acme.Address"}'
                ),
                "required": True,
                "properties": [
                    {
                        "name": "city",
                        "logicalType": "string",
                        "physicalType": "string",
                        "required": True,
                    }
                ],
                "customProperties": [
                    {"property": "typeName", "value": "Address"},
                    {"property": "connect.name", "value": "com.acme.Address", "vendor": "avro"},
                ],
            },
        ),
    ],
    ids=["primitive", "nullable", "array_items", "map_values", "nested_record"],
)
def test_read_should_read_type_extra_attribute_as_avro_custom_property(avro_type, expected):
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "field", "type": avro_type}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result["field"].model_dump(exclude_unset=True)
    assert actual == expected


def test_read_should_read_unknown_logical_type_as_avro_custom_property():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "at", "type": {"type": "long", "logicalType": "iso-8601"}}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result["at"].model_dump(exclude_unset=True)
    expected = {
        "name": "at",
        "logicalType": "integer",
        "physicalType": '{"type": "long", "logicalType": "iso-8601"}',
        "logicalTypeOptions": {"format": "i64"},
        "required": True,
        "customProperties": [{"property": "logicalType", "value": "iso-8601", "vendor": "avro"}],
    }
    assert actual == expected


def test_read_should_put_type_parameters_before_other_custom_properties():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [
            {
                "name": "at",
                "type": {"type": "long", "logicalType": "timestamp-millis", "connect.version": 1},
                "pii": True,
            }
        ],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result["at"].model_dump(exclude_unset=True)["customProperties"]
    expected = [
        {"property": "timeUnit", "value": "millis"},
        {"property": "pii", "value": True},
        {"property": "connect.version", "value": 1, "vendor": "avro"},
    ]
    assert actual == expected


def test_read_should_read_record_extra_attribute_as_schema_custom_property():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "customer",
        "connect.name": "com.acme.Customer",
        "fields": [{"name": "id", "type": "long"}],
    }

    # Act
    result = AvroSchemaReader().read(avro_schema)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "customer",
        "customProperties": [{"property": "connect.name", "value": "com.acme.Customer"}],
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
    "avro_schema",
    [
        {"type": "enum", "name": "Status", "symbols": ["ACTIVE"]},
        [],
    ],
)
def test_read_should_raise_schema_error_when_input_is_not_record(avro_schema):
    # Act / Assert
    with pytest.raises(SchemaError, match="An Avro schema must be a record type"):
        AvroSchemaReader().read(avro_schema)


@pytest.mark.parametrize(
    "avro_type",
    [
        ["string", "long"],
        ["null", "string", "long"],
    ],
)
def test_read_should_raise_schema_error_when_union_has_more_than_one_non_null_type(avro_type):
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "id", "type": avro_type}],
    }

    # Act / Assert
    with pytest.raises(SchemaError, match="Unsupported Avro union"):
        AvroSchemaReader().read(avro_schema)


def test_read_should_raise_schema_error_when_type_references_named_type():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "home", "type": "users.address"}],
    }

    # Act / Assert
    with pytest.raises(SchemaError, match="Unsupported Avro type `users.address`"):
        AvroSchemaReader().read(avro_schema)


@pytest.mark.parametrize(
    "avro_schema, record_name",
    [
        ({"type": "record", "name": "users"}, "users"),
        (
            {
                "type": "record",
                "name": "users",
                "fields": [
                    {"name": "address", "type": {"type": "record", "name": "users.address"}}
                ],
            },
            "users.address",
        ),
    ],
)
def test_read_should_raise_schema_error_when_record_has_no_fields(avro_schema, record_name):
    # Act / Assert
    with pytest.raises(SchemaError, match=f"Avro record `{record_name}` has no fields"):
        AvroSchemaReader().read(avro_schema)


def test_read_should_raise_schema_error_when_field_has_no_name():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"type": "long"}],
    }

    # Act / Assert
    with pytest.raises(SchemaError, match="has no name"):
        AvroSchemaReader().read(avro_schema)


def test_read_should_raise_schema_error_when_field_has_no_type():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "id"}],
    }

    # Act / Assert
    with pytest.raises(SchemaError, match="Avro field `id` has no type"):
        AvroSchemaReader().read(avro_schema)


def test_read_should_raise_schema_error_when_decimal_has_no_precision():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "balance", "type": {"type": "bytes", "logicalType": "decimal"}}],
    }

    # Act / Assert
    with pytest.raises(SchemaError, match="has no precision"):
        AvroSchemaReader().read(avro_schema)


def test_read_should_raise_schema_error_when_type_refers_to_itself():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "Node",
        "fields": [{"name": "next", "type": ["null", "Node"], "default": None}],
    }

    # Act / Assert
    with pytest.raises(
        SchemaError,
        match="Avro type `Node` refers to itself, which a schema cannot represent",
    ):
        AvroSchemaReader().read(avro_schema)


def test_read_should_raise_schema_error_when_fixed_has_no_size():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "users",
        "fields": [{"name": "hash", "type": {"type": "fixed", "name": "Hash"}}],
    }

    # Act / Assert
    with pytest.raises(SchemaError, match="has no size"):
        AvroSchemaReader().read(avro_schema)
