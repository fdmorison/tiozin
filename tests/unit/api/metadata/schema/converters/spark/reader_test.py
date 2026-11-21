import pytest

from tiozin.api.metadata.schema.converters.spark import SparkSchemaReader
from tiozin.exceptions import SchemaError


def test_read_should_read_struct_field_as_property():
    # Arrange
    spark_schema = {
        "type": "struct",
        "fields": [{"name": "id", "type": "long", "nullable": True, "metadata": {}}],
    }

    # Act
    result = SparkSchemaReader().read(spark_schema)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {
                "name": "id",
                "logicalType": "integer",
                "physicalType": "long",
                "logicalTypeOptions": {"format": "i64"},
            }
        ],
    }
    assert actual == expected


@pytest.mark.parametrize(
    "spark_type, expected",
    [
        ("string", "string"),
        ("char(3)", "string"),
        ("varchar(10)", "string"),
        ("binary", "string"),
        ("boolean", "boolean"),
        ("date", "date"),
        ("timestamp", "timestamp"),
        ("timestamp_ntz", "timestamp"),
        ("byte", "integer"),
        ("short", "integer"),
        ("integer", "integer"),
        ("long", "integer"),
        ("float", "number"),
        ("double", "number"),
        ("decimal(10,2)", "number"),
    ],
)
def test_read_should_map_spark_type_to_logical_type(spark_type, expected):
    # Arrange
    spark_schema = {
        "type": "struct",
        "fields": [{"name": "field", "type": spark_type, "nullable": True, "metadata": {}}],
    }

    # Act
    result = SparkSchemaReader().read(spark_schema)

    # Assert
    actual = result["field"].logicalType
    assert actual == expected


def test_read_should_read_not_nullable_field_as_required():
    # Arrange
    spark_schema = {
        "type": "struct",
        "fields": [{"name": "id", "type": "long", "nullable": False, "metadata": {}}],
    }

    # Act
    result = SparkSchemaReader().read(spark_schema)

    # Assert
    actual = result["id"].required
    expected = True
    assert actual == expected


def test_read_should_read_comment_as_description():
    # Arrange
    spark_schema = {
        "type": "struct",
        "fields": [
            {"name": "id", "type": "long", "nullable": True, "metadata": {"comment": "Identifier"}}
        ],
    }

    # Act
    result = SparkSchemaReader().read(spark_schema)

    # Assert
    actual = result["id"].description
    expected = "Identifier"
    assert actual == expected


def test_read_should_read_attribute_metadata_as_attributes():
    # Arrange
    spark_schema = {
        "type": "struct",
        "fields": [
            {
                "name": "email",
                "type": "string",
                "nullable": True,
                "metadata": {"classification": "pii", "tags": ["contact"]},
            }
        ],
    }

    # Act
    result = SparkSchemaReader().read(spark_schema)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {
                "name": "email",
                "logicalType": "string",
                "physicalType": "string",
                "classification": "pii",
                "tags": ["contact"],
            }
        ],
    }
    assert actual == expected


def test_read_should_read_other_metadata_as_custom_properties():
    # Arrange
    spark_schema = {
        "type": "struct",
        "fields": [
            {"name": "email", "type": "string", "nullable": True, "metadata": {"source": "crm"}}
        ],
    }

    # Act
    result = SparkSchemaReader().read(spark_schema)

    # Assert
    actual = result["email"].model_dump(exclude_unset=True)["customProperties"]
    expected = [{"property": "source", "value": "crm"}]
    assert actual == expected


def test_read_should_read_custom_properties_list():
    # Arrange
    spark_schema = {
        "type": "struct",
        "fields": [
            {
                "name": "email",
                "type": "string",
                "nullable": True,
                "metadata": {
                    "customProperties": [
                        {"property": "source", "value": "crm", "description": "System of record"}
                    ]
                },
            }
        ],
    }

    # Act
    result = SparkSchemaReader().read(spark_schema)

    # Assert
    actual = result["email"].model_dump(exclude_unset=True)["customProperties"]
    expected = [{"property": "source", "value": "crm", "description": "System of record"}]
    assert actual == expected


def test_read_should_read_struct_as_object():
    # Arrange
    spark_schema = {
        "type": "struct",
        "fields": [
            {
                "name": "address",
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
    }

    # Act
    result = SparkSchemaReader().read(spark_schema)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {
                "name": "address",
                "logicalType": "object",
                "physicalType": (
                    '{"type": "struct", "fields": '
                    '[{"name": "city", "type": "string", "nullable": true, "metadata": {}}]}'
                ),
                "properties": [{"name": "city", "logicalType": "string", "physicalType": "string"}],
            }
        ],
    }
    assert actual == expected


def test_read_should_read_array_with_element_nullability():
    # Arrange
    spark_schema = {
        "type": "struct",
        "fields": [
            {
                "name": "tags",
                "type": {"type": "array", "elementType": "string", "containsNull": False},
                "nullable": True,
                "metadata": {},
            }
        ],
    }

    # Act
    result = SparkSchemaReader().read(spark_schema)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {
                "name": "tags",
                "logicalType": "array",
                "physicalType": '{"type": "array", "elementType": "string", "containsNull": false}',
                "items": {"logicalType": "string", "physicalType": "string", "required": True},
            }
        ],
    }
    assert actual == expected


def test_read_should_read_map_with_value_nullability():
    # Arrange
    spark_schema = {
        "type": "struct",
        "fields": [
            {
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
        ],
    }

    # Act
    result = SparkSchemaReader().read(spark_schema)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "properties": [
            {
                "name": "scores",
                "logicalType": "map",
                "physicalType": (
                    '{"type": "map", "keyType": "string", "valueType": "long", '
                    '"valueContainsNull": false}'
                ),
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


def test_read_should_read_struct_metadata_as_schema_attributes():
    # Arrange
    spark_schema = {
        "type": "struct",
        "fields": [{"name": "id", "type": "long", "nullable": True, "metadata": {}}],
        "metadata": {
            "name": "users",
            "description": "Registered users",
            "physicalType": "table",
            "tags": ["gold"],
            "customProperties": [{"property": "owner", "value": "sales"}],
        },
    }

    # Act
    result = SparkSchemaReader().read(spark_schema)

    # Assert
    actual = result.model_dump(exclude_unset=True)
    expected = {
        "name": "users",
        "description": "Registered users",
        "physicalType": "table",
        "tags": ["gold"],
        "customProperties": [{"property": "owner", "value": "sales"}],
        "properties": [
            {
                "name": "id",
                "logicalType": "integer",
                "physicalType": "long",
                "logicalTypeOptions": {"format": "i64"},
            }
        ],
    }
    assert actual == expected


@pytest.mark.parametrize(
    "spark_type, expected",
    [
        (
            "decimal(10,2)",
            {
                "name": "field",
                "logicalType": "number",
                "physicalType": "decimal(10,2)",
                "customProperties": [
                    {"property": "precision", "value": 10},
                    {"property": "scale", "value": 2},
                ],
            },
        ),
        (
            "varchar(10)",
            {
                "name": "field",
                "logicalType": "string",
                "physicalType": "varchar(10)",
                "logicalTypeOptions": {"maxLength": 10},
            },
        ),
        (
            "timestamp_ntz",
            {
                "name": "field",
                "logicalType": "timestamp",
                "physicalType": "timestamp_ntz",
                "customProperties": [{"property": "timeUnit", "value": "micros"}],
                "logicalTypeOptions": {"timezone": False},
            },
        ),
        (
            "char(3)",
            {
                "name": "field",
                "logicalType": "string",
                "physicalType": "char(3)",
                "logicalTypeOptions": {"minLength": 3, "maxLength": 3},
            },
        ),
        (
            "short",
            {
                "name": "field",
                "logicalType": "integer",
                "physicalType": "short",
                "logicalTypeOptions": {"format": "i16"},
            },
        ),
        (
            "binary",
            {
                "name": "field",
                "logicalType": "string",
                "physicalType": "binary",
                "customProperties": [{"property": "binary", "value": True}],
            },
        ),
        (
            "time(3)",
            {
                "name": "field",
                "logicalType": "time",
                "physicalType": "time(3)",
                "customProperties": [{"property": "timeUnit", "value": "millis"}],
            },
        ),
        (
            "time(6)",
            {
                "name": "field",
                "logicalType": "time",
                "physicalType": "time(6)",
                "customProperties": [{"property": "timeUnit", "value": "micros"}],
            },
        ),
        (
            "time",
            {
                "name": "field",
                "logicalType": "time",
                "physicalType": "time",
                "customProperties": [{"property": "timeUnit", "value": "micros"}],
            },
        ),
    ],
)
def test_read_should_read_spark_type_into_canonical_attributes(spark_type, expected):
    # Arrange
    spark_schema = {
        "type": "struct",
        "fields": [{"name": "field", "type": spark_type, "nullable": True, "metadata": {}}],
    }

    # Act
    result = SparkSchemaReader().read(spark_schema)

    # Assert
    actual = result["field"].model_dump(exclude_unset=True)
    assert actual == expected


def test_read_should_prefer_metadata_custom_property_over_implied_parameter():
    # Arrange
    spark_schema = {
        "type": "struct",
        "fields": [
            {
                "name": "at",
                "type": "timestamp",
                "nullable": True,
                "metadata": {"physicalType": "long", "timeUnit": "millis"},
            }
        ],
    }

    # Act
    result = SparkSchemaReader().read(spark_schema)

    # Assert
    actual = result["at"].model_dump(exclude_unset=True)
    expected = {
        "name": "at",
        "logicalType": "timestamp",
        "physicalType": "long",
        "customProperties": [{"property": "timeUnit", "value": "millis"}],
        "logicalTypeOptions": {"timezone": True},
    }
    assert actual == expected


@pytest.mark.parametrize(
    "spark_schema",
    [
        {"type": "array", "elementType": "long", "containsNull": True},
        [],
    ],
)
def test_read_should_raise_schema_error_when_input_is_not_struct(spark_schema):
    # Act / Assert
    with pytest.raises(SchemaError, match="A Spark schema must be a struct type"):
        SparkSchemaReader().read(spark_schema)


def test_read_should_raise_schema_error_when_spark_type_is_unsupported():
    # Arrange
    spark_schema = {
        "type": "struct",
        "fields": [{"name": "point", "type": {"type": "udt"}, "nullable": True, "metadata": {}}],
    }

    # Act / Assert
    with pytest.raises(SchemaError, match="Unsupported Spark type `udt`"):
        SparkSchemaReader().read(spark_schema)
