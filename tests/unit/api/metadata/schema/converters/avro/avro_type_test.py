import pytest

from tiozin.api.metadata.schema.converters.avro.avro_type import AvroType
from tiozin.exceptions import SchemaError


@pytest.mark.parametrize("json_value", [["null", "long"], ["long", "null"]])
def test_is_nullable_should_pass_when_type_is_union_with_null(json_value):
    # Act
    result = AvroType(json_value)

    # Assert
    assert result.is_nullable


def test_is_nullable_should_not_pass_when_type_is_not_union():
    # Act
    result = AvroType("long")

    # Assert
    assert not result.is_nullable


@pytest.mark.parametrize(
    "json_value, expected",
    [
        (["null", "long"], "long"),
        (["long", "null"], "long"),
        ("long", "long"),
    ],
)
def test_non_null_should_return_type_without_null(json_value, expected):
    # Act
    result = AvroType(json_value).non_null

    # Assert
    actual = result.json_value
    assert actual == expected


@pytest.mark.parametrize(
    "json_value, expected",
    [
        ("long", "long"),
        ({"type": "long"}, "long"),
        ({"type": "long", "logicalType": "timestamp-millis"}, "timestamp-millis"),
        ({"type": "bytes", "logicalType": "decimal", "precision": 10}, "decimal"),
        ({"type": "record", "name": "users", "fields": []}, "record"),
        ({"type": "array", "items": "string"}, "array"),
        ({"type": "map", "values": "long"}, "map"),
        ({"type": "enum", "name": "status", "symbols": ["A"]}, "enum"),
        ({"type": "fixed", "name": "hash", "size": 16}, "fixed"),
    ],
)
def test_type_name_should_name_avro_type(json_value, expected):
    # Act
    result = AvroType(json_value).type_name

    # Assert
    actual = result
    assert actual == expected


@pytest.mark.parametrize(
    "json_value, expected",
    [
        ("string", "string"),
        ("bytes", "string"),
        ("int", "integer"),
        ("double", "number"),
        ("boolean", "boolean"),
        ({"type": "int", "logicalType": "date"}, "date"),
        ({"type": "long", "logicalType": "time-micros"}, "time"),
        ({"type": "long", "logicalType": "timestamp-micros"}, "timestamp"),
        ({"type": "bytes", "logicalType": "decimal", "precision": 10}, "number"),
        ({"type": "record", "name": "users", "fields": []}, "object"),
        ({"type": "array", "items": "string"}, "array"),
        ({"type": "map", "values": "long"}, "map"),
        ({"type": "enum", "name": "status", "symbols": ["A"]}, "string"),
        ({"type": "fixed", "name": "hash", "size": 16}, "string"),
    ],
)
def test_logical_type_should_map_avro_type_to_logical_type(json_value, expected):
    # Act
    result = AvroType(json_value).logical_type

    # Assert
    actual = result
    assert actual == expected


@pytest.mark.parametrize(
    "json_value, expected",
    [
        ("string", "string"),
        ("bytes", "bytes"),
        ("boolean", "boolean"),
        ("int", "int"),
        ("long", "long"),
        ("float", "float"),
        ("double", "double"),
        ({"type": "long"}, '{"type": "long"}'),
        ({"type": "string", "logicalType": "uuid"}, '{"type": "string", "logicalType": "uuid"}'),
        ({"type": "int", "logicalType": "date"}, '{"type": "int", "logicalType": "date"}'),
        (
            {"type": "long", "logicalType": "timestamp-millis"},
            '{"type": "long", "logicalType": "timestamp-millis"}',
        ),
        (
            {"type": "bytes", "logicalType": "decimal", "precision": 10, "scale": 2},
            '{"type": "bytes", "logicalType": "decimal", "precision": 10, "scale": 2}',
        ),
        (
            {"type": "fixed", "name": "hash", "size": 16},
            '{"type": "fixed", "name": "hash", "size": 16}',
        ),
        (
            {"type": "enum", "name": "status", "symbols": ["A"]},
            '{"type": "enum", "name": "status", "symbols": ["A"]}',
        ),
        (
            {"type": "record", "name": "users", "fields": []},
            '{"type": "record", "name": "users", "fields": []}',
        ),
        ({"type": "array", "items": "string"}, '{"type": "array", "items": "string"}'),
        ({"type": "map", "values": "long"}, '{"type": "map", "values": "long"}'),
        (["null", "string"], '["null", "string"]'),
        ("Address", "Address"),
    ],
)
def test_physical_type_should_be_type_as_written(json_value, expected):
    # Act
    result = AvroType(json_value).physical_type

    # Assert
    actual = result
    assert actual == expected


def test_type_parameters_should_be_empty_when_type_has_no_parameters():
    # Act
    result = AvroType("long").type_parameters

    # Assert
    actual = result
    expected = []
    assert actual == expected


@pytest.mark.parametrize(
    "json_value, expected",
    [
        (
            {"type": "bytes", "logicalType": "decimal", "precision": 10, "scale": 2},
            [{"property": "precision", "value": 10}, {"property": "scale", "value": 2}],
        ),
        (
            {"type": "bytes", "logicalType": "decimal", "precision": 10},
            [{"property": "precision", "value": 10}],
        ),
        (
            {
                "type": "fixed",
                "name": "price",
                "size": 8,
                "logicalType": "decimal",
                "precision": 10,
                "scale": 2,
            },
            [
                {"property": "precision", "value": 10},
                {"property": "scale", "value": 2},
                {"property": "typeSize", "value": 8},
            ],
        ),
        (
            {"type": "fixed", "name": "hash", "size": 16},
            [{"property": "binary", "value": True}, {"property": "typeSize", "value": 16}],
        ),
        (
            "bytes",
            [{"property": "binary", "value": True}],
        ),
    ],
    ids=["decimal", "decimal_without_scale", "decimal_on_fixed", "fixed", "bytes"],
)
def test_type_parameters_should_hold_binary_size_precision_and_scale(json_value, expected):
    # Act
    result = AvroType(json_value).type_parameters

    # Assert
    actual = result
    assert actual == expected


@pytest.mark.parametrize(
    "json_value, expected",
    [
        (
            {"type": "int", "logicalType": "time-millis"},
            [{"property": "timeUnit", "value": "millis"}],
        ),
        (
            {"type": "long", "logicalType": "time-micros"},
            [{"property": "timeUnit", "value": "micros"}],
        ),
        (
            {"type": "long", "logicalType": "timestamp-millis"},
            [{"property": "timeUnit", "value": "millis"}],
        ),
        (
            {"type": "long", "logicalType": "timestamp-micros"},
            [{"property": "timeUnit", "value": "micros"}],
        ),
        (
            {"type": "long", "logicalType": "timestamp-nanos"},
            [{"property": "timeUnit", "value": "nanos"}],
        ),
        (
            {"type": "long", "logicalType": "local-timestamp-millis"},
            [{"property": "timeUnit", "value": "millis"}],
        ),
        (
            {"type": "long", "logicalType": "local-timestamp-micros"},
            [{"property": "timeUnit", "value": "micros"}],
        ),
        (
            {"type": "long", "logicalType": "local-timestamp-nanos"},
            [{"property": "timeUnit", "value": "nanos"}],
        ),
    ],
)
def test_type_parameters_should_hold_time_unit_of_temporal_type(json_value, expected):
    # Act
    result = AvroType(json_value).type_parameters

    # Assert
    actual = result
    assert actual == expected


@pytest.mark.parametrize(
    "json_value, expected",
    [
        ("int", {"format": "i32"}),
        ("long", {"format": "i64"}),
        ("float", {"format": "f32"}),
        ("double", {"format": "f64"}),
        ({"type": "long", "logicalType": "timestamp-millis"}, {"timezone": True}),
        ({"type": "long", "logicalType": "timestamp-nanos"}, {"timezone": True}),
        ({"type": "long", "logicalType": "local-timestamp-micros"}, {"timezone": False}),
        ({"type": "string", "logicalType": "uuid"}, {"format": "uuid"}),
    ],
)
def test_logical_type_options_should_hold_options_the_type_implies(json_value, expected):
    # Act
    result = AvroType(json_value).logical_type_options

    # Assert
    actual = result
    assert actual == expected


@pytest.mark.parametrize(
    "json_value",
    [
        "string",
        "bytes",
        {"type": "long", "logicalType": "time-micros"},
    ],
)
def test_logical_type_options_should_be_none_when_type_implies_none(json_value):
    # Act
    result = AvroType(json_value).logical_type_options

    # Assert
    assert result is None


def test_enum_values_should_hold_enum_symbols():
    # Act
    result = AvroType({"type": "enum", "name": "status", "symbols": ["A", "B"]}).enum_values

    # Assert
    actual = result
    expected = [{"value": "A"}, {"value": "B"}]
    assert actual == expected


def test_enum_values_should_be_none_when_type_is_not_enum():
    # Act
    result = AvroType("string").enum_values

    # Assert
    assert result is None


@pytest.mark.parametrize(
    "json_value, expected",
    [
        (
            {"type": "fixed", "name": "MD5", "size": 16},
            [{"property": "typeName", "value": "MD5"}],
        ),
        (
            {"type": "record", "name": "Address", "namespace": "com.acme.geo", "fields": []},
            [
                {"property": "typeName", "value": "Address"},
                {"property": "namespace", "value": "com.acme.geo"},
            ],
        ),
    ],
    ids=["without_namespace", "with_namespace"],
)
def test_custom_properties_should_hold_name_of_named_type(json_value, expected):
    # Act
    result = AvroType(json_value).custom_properties

    # Assert
    actual = result
    assert actual == expected


def test_custom_properties_should_be_empty_when_type_is_not_named():
    # Act
    result = AvroType({"type": "array", "items": "string"}).custom_properties

    # Assert
    actual = result
    expected = []
    assert actual == expected


@pytest.mark.parametrize(
    "json_value, expected",
    [
        (
            "long",
            {
                "logicalType": "integer",
                "physicalType": "long",
                "logicalTypeOptions": {"format": "i64"},
            },
        ),
        (
            {"type": "enum", "name": "status", "symbols": ["A"]},
            {
                "logicalType": "string",
                "physicalType": '{"type": "enum", "name": "status", "symbols": ["A"]}',
                "enum": [{"value": "A"}],
            },
        ),
        (
            {"type": "long", "logicalType": "timestamp-millis"},
            {
                "logicalType": "timestamp",
                "physicalType": '{"type": "long", "logicalType": "timestamp-millis"}',
                "logicalTypeOptions": {"timezone": True},
            },
        ),
    ],
)
def test_attributes_should_hold_property_attributes_the_type_implies(json_value, expected):
    # Act
    result = AvroType(json_value).attributes

    # Assert
    actual = result
    assert actual == expected


def test_fields_should_return_record_fields():
    # Act
    result = AvroType(
        {"type": "record", "name": "users", "fields": [{"name": "id", "type": "long"}]}
    ).fields

    # Assert
    actual = result
    expected = [{"name": "id", "type": "long"}]
    assert actual == expected


def test_items_should_return_array_item_type():
    # Act
    result = AvroType({"type": "array", "items": ["null", "string"]}).items

    # Assert
    actual = result.json_value
    expected = ["null", "string"]
    assert actual == expected


def test_values_should_return_map_value_type():
    # Act
    result = AvroType({"type": "map", "values": "long"}).values

    # Assert
    actual = result.json_value
    expected = "long"
    assert actual == expected


@pytest.mark.parametrize(
    "json_value",
    [
        ["string", "long"],
        ["null", "string", "long"],
        ["null", "null"],
    ],
)
def test_non_null_should_raise_schema_error_when_union_is_unsupported(json_value):
    # Act / Assert
    with pytest.raises(SchemaError, match="Unsupported Avro union"):
        _ = AvroType(json_value).non_null


@pytest.mark.parametrize("json_value", ["users.address", {"type": "unknown"}])
def test_type_name_should_raise_schema_error_when_type_is_unsupported(json_value):
    # Act / Assert
    with pytest.raises(SchemaError, match="Unsupported Avro type"):
        _ = AvroType(json_value).type_name


def test_type_parameters_should_raise_schema_error_when_decimal_has_no_precision():
    # Act / Assert
    with pytest.raises(SchemaError, match="has no precision"):
        _ = AvroType({"type": "bytes", "logicalType": "decimal"}).type_parameters


def test_enum_values_should_raise_schema_error_when_enum_has_no_symbols():
    # Act / Assert
    with pytest.raises(SchemaError, match="Unsupported Avro type"):
        _ = AvroType({"type": "enum", "name": "status"}).enum_values


def test_fields_should_raise_schema_error_when_record_has_no_fields():
    # Act / Assert
    with pytest.raises(SchemaError, match="Avro record `users` has no fields"):
        _ = AvroType({"type": "record", "name": "users"}).fields


def test_items_should_raise_schema_error_when_array_has_no_items():
    # Act / Assert
    with pytest.raises(SchemaError, match="Unsupported Avro type"):
        _ = AvroType({"type": "array"}).items


def test_values_should_raise_schema_error_when_map_has_no_values():
    # Act / Assert
    with pytest.raises(SchemaError, match="Unsupported Avro type"):
        _ = AvroType({"type": "map"}).values


def test_type_parameters_should_raise_schema_error_when_fixed_has_no_size():
    # Act / Assert
    with pytest.raises(SchemaError, match="has no size"):
        _ = AvroType({"type": "fixed", "name": "hash"}).type_parameters
