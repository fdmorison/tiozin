from importlib.metadata import version
from unittest.mock import MagicMock, call, patch

import pytest
import yaml

from tiozin import Schema
from tiozin.api.metadata.schema.converters.spark import SparkSchemaWriter
from tiozin.api.metadata.schema.model import Map, Property
from tiozin.exceptions import SchemaError


def test_write_should_write_struct_field_per_property():
    # Arrange
    schema = Schema(name="users").integer("id", physicalType="long")

    # Act
    result = SparkSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {
        "type": "struct",
        "fields": [{"name": "id", "type": "long", "nullable": True, "metadata": {}}],
        "metadata": {"name": "users"},
    }
    assert actual == expected


def test_writer_should_target_installed_pyspark_version_by_default():
    # Act
    result = SparkSchemaWriter()

    # Assert
    actual = result.version
    expected = version("pyspark")
    assert actual == expected


@pytest.mark.parametrize(
    "spark_version",
    ["4.1", "4.1.0.dev1", "4.1rc1", "4.1.0+databricks", "v4.1"],
)
def test_write_should_accept_version_starting_with_major_minor(spark_version):
    # Arrange
    schema = Schema(name="users").time("starts_at")

    # Act
    result = SparkSchemaWriter(version=spark_version).write(schema)

    # Assert
    actual = result["fields"][0]["type"]
    expected = "time(6)"
    assert actual == expected


@pytest.mark.parametrize(
    "logical_type, expected",
    [
        ("string", "string"),
        ("integer", "long"),
        ("number", "double"),
        ("boolean", "boolean"),
        ("date", "date"),
        ("timestamp", "timestamp"),
    ],
)
def test_write_should_pick_spark_type_from_logical_type(logical_type, expected):
    # Arrange
    schema = Schema(name="users").add("field", logical_type)

    # Act
    result = SparkSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]["type"]
    assert actual == expected


@pytest.mark.parametrize(
    "prop, expected",
    [
        (
            Property(name="starts_at", logicalType="time"),
            {"name": "starts_at", "type": "time(6)", "nullable": True, "metadata": {}},
        ),
        (
            Property(name="starts_at", logicalType="time", timeUnit="micros"),
            {"name": "starts_at", "type": "time(6)", "nullable": True, "metadata": {}},
        ),
        (
            Property(name="starts_at", logicalType="time", timeUnit="millis"),
            {"name": "starts_at", "type": "time(3)", "nullable": True, "metadata": {}},
        ),
    ],
    ids=["default", "micros", "millis"],
)
def test_write_should_write_time_as_spark_time_of_its_unit(prop, expected):
    # Arrange
    schema = Schema(name="users", properties=[prop])

    # Act
    result = SparkSchemaWriter(version="4.1").write(schema)

    # Assert
    actual = result["fields"][0]
    assert actual == expected


@pytest.mark.parametrize(
    "prop, expected",
    [
        (
            Property(name="opens_at", logicalType="time"),
            {
                "type": "struct",
                "fields": [
                    {
                        "name": "opens_at",
                        "type": "time(6)",
                        "nullable": True,
                        "metadata": {},
                    }
                ],
                "metadata": {"name": "t"},
            },
        ),
        (
            Property(name="addr", properties=[Property(name="city", logicalType="string")]),
            {
                "type": "struct",
                "fields": [
                    {
                        "name": "addr",
                        "type": {
                            "type": "struct",
                            "fields": [
                                {"name": "city", "type": "string", "nullable": True, "metadata": {}}
                            ],
                        },
                        "nullable": True,
                        "metadata": {},
                    }
                ],
                "metadata": {"name": "t"},
            },
        ),
    ],
    ids=["time", "object_without_logical_type"],
)
def test_write_should_write_metadata_as_plain_json(prop, expected):
    # Arrange
    schema = Schema(name="t", properties=[prop])

    # Act
    result = SparkSchemaWriter(version="4.1").write(schema)

    # Assert
    actual = yaml.safe_load(yaml.safe_dump(result))
    assert actual == expected


def test_write_should_write_object_without_logical_type_that_reads_back_as_object():
    # Arrange
    schema = Schema(
        name="t",
        properties=[
            Property(name="addr", properties=[Property(name="city", logicalType="string")])
        ],
    )

    # Act
    result = SparkSchemaWriter().write(schema)

    # Assert
    actual = Schema.from_spark(result)["addr"].logicalType
    expected = "object"
    assert actual == expected


@pytest.mark.parametrize(
    "logical_type, physical_type, expected",
    [
        ("integer", "string", "long"),
        ("integer", "short", "long"),
        ("integer", "int", "long"),
        ("integer", "smallint", "long"),
        ("integer", "tinyint", "long"),
        ("number", "decimal(10,2)", "double"),
        ("string", "char(3)", "string"),
        ("string", "varchar(10)", "string"),
        ("string", "varchar", "string"),
        ("string", "VARCHAR2", "string"),
        ("string", "binary", "string"),
    ],
)
def test_write_should_ignore_physical_type_when_picking_spark_type(
    logical_type, physical_type, expected
):
    # Arrange
    schema = Schema(name="users").add("field", logical_type, physicalType=physical_type)

    # Act
    result = SparkSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]["type"]
    assert actual == expected


@pytest.mark.parametrize(
    "physical_type",
    [
        "bigint",
        "int",
        "decimal(10,0)",
    ],
)
def test_write_should_not_write_physical_type_in_metadata(physical_type):
    # Arrange
    schema = Schema(name="users").integer("id", physicalType=physical_type)

    # Act
    result = SparkSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]
    expected = {"name": "id", "type": "long", "nullable": True, "metadata": {}}
    assert actual == expected


@pytest.mark.parametrize(
    "logical_type, size_format, expected",
    [
        ("integer", "i8", "byte"),
        ("integer", "i16", "short"),
        ("integer", "i32", "integer"),
        ("integer", "u8", "short"),
        ("integer", "u16", "integer"),
        ("integer", "i64", "long"),
        ("integer", "u32", "long"),
        ("number", "f32", "float"),
        ("number", "f64", "double"),
    ],
)
def test_write_should_pick_spark_size_from_format(logical_type, size_format, expected):
    # Arrange
    schema = Schema(name="users").add(
        "field", logical_type, logicalTypeOptions={"format": size_format}
    )

    # Act
    result = SparkSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]["type"]
    assert actual == expected


def test_write_should_write_binary_string_as_binary():
    # Arrange
    schema = Schema(name="users").string(
        "payload",
        customProperties=[{"property": "binary", "value": True}],
    )

    # Act
    result = SparkSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]["type"]
    expected = "binary"
    assert actual == expected


@pytest.mark.parametrize(
    "logical_type_options, expected",
    [
        ({"minLength": 3, "maxLength": 3}, "char(3)"),
        ({"maxLength": 10}, "varchar(10)"),
        ({"minLength": 2, "maxLength": 10}, "varchar(10)"),
    ],
    ids=["fixed_length", "max_length", "length_range"],
)
def test_write_should_write_char_only_when_min_and_max_length_match(logical_type_options, expected):
    # Arrange
    schema = Schema(name="users").string("code", logicalTypeOptions=logical_type_options)

    # Act
    result = SparkSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]["type"]
    assert actual == expected


def test_write_should_write_required_property_as_not_nullable():
    # Arrange
    schema = Schema(name="users").integer("id", physicalType="long", required=True)

    # Act
    result = SparkSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]
    expected = {"name": "id", "type": "long", "nullable": False, "metadata": {}}
    assert actual == expected


def test_write_should_keep_explicit_optional_in_metadata():
    # Arrange
    schema = Schema(name="users").integer("id", physicalType="long", required=False)

    # Act
    result = SparkSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]
    expected = {"name": "id", "type": "long", "nullable": True, "metadata": {"required": False}}
    assert actual == expected


def test_write_should_write_description_as_comment():
    # Arrange
    schema = Schema(name="users").string("name", physicalType="string", description="Full name")

    # Act
    result = SparkSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]["metadata"]
    expected = {"comment": "Full name"}
    assert actual == expected


def test_write_should_write_property_attributes_in_metadata():
    # Arrange
    schema = Schema(name="users").string(
        "email",
        physicalType="string",
        classification="pii",
        tags=["contact"],
        primaryKey=True,
    )

    # Act
    result = SparkSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]["metadata"]
    expected = {"classification": "pii", "tags": ["contact"], "primaryKey": True}
    assert actual == expected


def test_write_should_write_plain_custom_property_as_metadata_key():
    # Arrange
    schema = Schema(name="users").string(
        "email",
        physicalType="string",
        customProperties=[{"property": "source", "value": "crm"}],
    )

    # Act
    result = SparkSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]["metadata"]
    expected = {"source": "crm"}
    assert actual == expected


@pytest.mark.parametrize(
    "custom_property",
    [
        {"property": "source", "value": "crm", "description": "System of record"},
        {"property": "source", "value": "crm", "id": "cp-1"},
        {"property": "classification", "value": "crm"},
        {"property": "comment", "value": "crm"},
    ],
)
def test_write_should_write_custom_properties_list_when_one_is_not_plain(custom_property):
    # Arrange
    schema = Schema(name="users").string(
        "email",
        physicalType="string",
        customProperties=[{"property": "owner", "value": "sales"}, custom_property],
    )

    # Act
    result = SparkSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]["metadata"]
    expected = {
        "customProperties": [{"property": "owner", "value": "sales"}, custom_property],
    }
    assert actual == expected


def test_write_should_write_empty_struct_metadata_when_schema_has_no_attributes():
    # Arrange
    schema = Schema().string("name", physicalType="string")

    # Act
    result = SparkSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {
        "type": "struct",
        "fields": [{"name": "name", "type": "string", "nullable": True, "metadata": {}}],
        "metadata": {},
    }
    assert actual == expected


def test_write_should_write_schema_attributes_as_struct_metadata():
    # Arrange
    schema = Schema(
        name="users",
        description="Registered users",
        physicalType="table",
        tags=["gold"],
        customProperties=[{"property": "owner", "value": "sales"}],
    ).string("name", physicalType="string")

    # Act
    result = SparkSchemaWriter().write(schema)

    # Assert
    actual = result
    expected = {
        "type": "struct",
        "fields": [{"name": "name", "type": "string", "nullable": True, "metadata": {}}],
        "metadata": {
            "name": "users",
            "description": "Registered users",
            "physicalType": "table",
            "tags": ["gold"],
            "customProperties": [{"property": "owner", "value": "sales"}],
        },
    }
    assert actual == expected


def test_write_should_write_object_as_struct():
    # Arrange
    schema = (
        Schema(name="users")
        .object("address")
        .string("address.city", physicalType="string", description="City name")
    )

    # Act
    result = SparkSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]
    expected = {
        "name": "address",
        "type": {
            "type": "struct",
            "fields": [
                {
                    "name": "city",
                    "type": "string",
                    "nullable": True,
                    "metadata": {"comment": "City name"},
                }
            ],
        },
        "nullable": True,
        "metadata": {},
    }
    assert actual == expected


def test_write_should_write_array_with_element_nullability():
    # Arrange
    schema = Schema(
        name="users",
        properties=[
            Property(
                name="tags",
                logicalType="array",
                items=Property(logicalType="string", physicalType="string", required=True),
            )
        ],
    )

    # Act
    result = SparkSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]
    expected = {
        "name": "tags",
        "type": {"type": "array", "elementType": "string", "containsNull": False},
        "nullable": True,
        "metadata": {},
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
                map=Map(
                    key=Property(logicalType="string", physicalType="string"),
                    value=Property(logicalType="integer", physicalType="long", required=True),
                ),
            )
        ],
    )

    # Act
    result = SparkSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]
    expected = {
        "name": "scores",
        "type": {
            "type": "map",
            "keyType": "string",
            "valueType": "long",
            "valueContainsNull": False,
        },
        "nullable": True,
        "metadata": {},
    }
    assert actual == expected


@pytest.mark.parametrize(
    "required, expected",
    [
        (True, {"map": {"key": {"required": True}}}),
        (False, {"map": {"key": {"required": False}}}),
    ],
)
def test_write_should_keep_explicit_map_key_required_in_metadata(required, expected):
    # Arrange
    schema = Schema(
        name="users",
        properties=[
            Property(
                name="scores",
                logicalType="map",
                map=Map(
                    key=Property(logicalType="string", physicalType="string", required=required),
                    value=Property(logicalType="integer", physicalType="long"),
                ),
            )
        ],
    )

    # Act
    result = SparkSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]["metadata"]
    assert actual == expected


@pytest.mark.parametrize(
    "prop, expected",
    [
        (
            Property(
                name="field",
                logicalType="number",
                physicalType="decimal",
                customProperties=[
                    {"property": "precision", "value": 10},
                    {"property": "scale", "value": 2},
                ],
            ),
            {"name": "field", "type": "decimal(10,2)", "nullable": True, "metadata": {}},
        ),
        (
            Property(
                name="field",
                logicalType="number",
                physicalType="decimal",
                customProperties=[{"property": "precision", "value": 10}],
            ),
            {"name": "field", "type": "decimal(10,0)", "nullable": True, "metadata": {}},
        ),
        (
            Property(
                name="field",
                logicalType="string",
                physicalType="varchar",
                logicalTypeOptions={"maxLength": 10},
            ),
            {"name": "field", "type": "varchar(10)", "nullable": True, "metadata": {}},
        ),
        (
            Property(
                name="field",
                logicalType="timestamp",
                physicalType="timestamp_ntz",
                logicalTypeOptions={"timezone": False},
            ),
            {"name": "field", "type": "timestamp_ntz", "nullable": True, "metadata": {}},
        ),
    ],
    ids=["decimal", "decimal_without_scale", "varchar", "timestamp_ntz"],
)
def test_write_should_write_spark_type_from_parameters_and_options(prop, expected):
    # Arrange
    schema = Schema(properties=[prop])

    # Act
    result = SparkSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]
    assert actual == expected


def test_write_should_write_decimal_on_fixed_and_keep_type_size_in_metadata():
    # Arrange
    schema = Schema(
        properties=[
            Property(
                name="price",
                logicalType="number",
                physicalType="fixed",
                customProperties=[
                    {"property": "precision", "value": 10},
                    {"property": "scale", "value": 2},
                    {"property": "typeSize", "value": 8},
                ],
            )
        ]
    )

    # Act
    result = SparkSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]
    expected = {
        "name": "price",
        "type": "decimal(10,2)",
        "nullable": True,
        "metadata": {"typeSize": 8},
    }
    assert actual == expected


def test_write_should_keep_time_unit_spark_does_not_imply_in_metadata():
    # Arrange
    schema = Schema(
        properties=[
            Property(
                name="at",
                logicalType="timestamp",
                physicalType="long",
                logicalTypeOptions={"timezone": True},
                customProperties=[{"property": "timeUnit", "value": "millis"}],
            )
        ]
    )

    # Act
    result = SparkSchemaWriter().write(schema)

    # Assert
    actual = result["fields"][0]
    expected = {
        "name": "at",
        "type": "timestamp",
        "nullable": True,
        "metadata": {"timeUnit": "millis"},
    }
    assert actual == expected


def test_write_should_raise_schema_error_when_map_lacks_key():
    # Arrange
    schema = Schema(
        name="users",
        properties=[
            Property(
                name="scores",
                logicalType="map",
                map=Map(value=Property(logicalType="integer")),
            )
        ],
    )

    # Act / Assert
    with pytest.raises(SchemaError):
        SparkSchemaWriter().write(schema)


def test_write_should_raise_schema_error_when_property_has_no_type():
    # Arrange
    schema = Schema(name="users", properties=[Property(name="anything")])

    # Act / Assert
    with pytest.raises(SchemaError):
        SparkSchemaWriter().write(schema)


def test_write_should_raise_schema_error_when_spark_has_no_type_for_format():
    # Arrange
    schema = Schema(name="users").integer("id", logicalTypeOptions={"format": "i128"})

    # Act / Assert
    with pytest.raises(SchemaError, match="Property `id` has no Spark type for format `i128`"):
        SparkSchemaWriter().write(schema)


def test_write_should_write_time_in_nanos_as_finest_spark_time():
    # Arrange
    schema = Schema(name="users").time("starts_at", timeUnit="nanos")

    # Act
    result = SparkSchemaWriter(version="4.1").write(schema)

    # Assert
    actual = result["fields"][0]
    expected = {
        "name": "starts_at",
        "type": "time(6)",
        "nullable": True,
        "metadata": {"timeUnit": "nanos"},
    }
    assert actual == expected


@pytest.mark.parametrize("spark_version", ["3.5", "4.1"])
@patch("tiozin.api.loggable.logs.get_logger")
def test_write_should_warn_that_spark_truncates_time_in_nanos(get_logger: MagicMock, spark_version):
    # Arrange
    schema = Schema(name="users").time("starts_at", timeUnit="nanos")

    # Act
    SparkSchemaWriter(version=spark_version).write(schema)

    # Assert
    actual = get_logger.return_value.warning.call_args_list
    expected = [
        call(
            "Property `starts_at` is a time in nanos, but Spark times go up to micros, "
            "so Spark truncates its values when it reads the data"
        )
    ]
    assert actual == expected


@pytest.mark.parametrize("spark_version", ["3.5", "4.0"])
def test_write_should_write_time_as_timestamp_ntz_when_spark_has_no_time_type(spark_version):
    # Arrange
    schema = Schema(name="users").time("starts_at")

    # Act
    result = SparkSchemaWriter(version=spark_version).write(schema)

    # Assert
    actual = result["fields"][0]
    expected = {
        "name": "starts_at",
        "type": "timestamp_ntz",
        "nullable": True,
        "metadata": {"logicalType": "time"},
    }
    assert actual == expected


def test_write_should_keep_time_unit_in_metadata_when_spark_has_no_time_type():
    # Arrange
    schema = Schema(name="users").time("starts_at", timeUnit="millis")

    # Act
    result = SparkSchemaWriter(version="3.5").write(schema)

    # Assert
    actual = result["fields"][0]
    expected = {
        "name": "starts_at",
        "type": "timestamp_ntz",
        "nullable": True,
        "metadata": {"logicalType": "time", "timeUnit": "millis"},
    }
    assert actual == expected


@pytest.mark.parametrize("spark_version", ["4", "abc"])
def test_writer_should_raise_schema_error_when_version_is_invalid(spark_version):
    # Act / Assert
    with pytest.raises(SchemaError, match=r"expected major\.minor such as 4\.1"):
        SparkSchemaWriter(version=spark_version)
