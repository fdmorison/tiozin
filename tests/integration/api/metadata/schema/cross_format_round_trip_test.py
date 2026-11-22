import json
from pathlib import Path

import pytest

from tiozin import Schema


def without_physical_type(value):
    """
    The dumped schema without its physical types, at every level. The physical
    type is the type as the last format read wrote it, so it changes on every
    hop by design.
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
def test_avro_schema_should_survive_spark_round_trip(schema_file):
    # Arrange
    schema = Schema.from_avro(json.loads(Path(f"tests/mocks/schemas/{schema_file}").read_text()))

    # Act
    result = Schema.from_spark(schema.to_spark(time_type="time"))

    # Assert
    actual = without_physical_type(result.model_dump(mode="json", exclude_unset=True))
    expected = without_physical_type(schema.model_dump(mode="json", exclude_unset=True))
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
def test_avro_schema_should_be_written_back_after_spark_round_trip(schema_file):
    # Arrange
    avro_schema = json.loads(Path(f"tests/mocks/schemas/{schema_file}").read_text())
    schema = Schema.from_spark(Schema.from_avro(avro_schema).to_spark(time_type="time"))

    # Act
    result = schema.to_avro()

    # Assert
    actual = result
    expected = avro_schema
    assert actual == expected


@pytest.mark.parametrize(
    "schema_file",
    [
        "spark_struct_with_parameterized_types.json",
        "spark_struct_with_metadata.json",
        "spark_struct_with_nested_types.json",
    ],
)
def test_spark_schema_should_survive_avro_round_trip(schema_file):
    # Arrange
    schema = Schema.from_spark(json.loads(Path(f"tests/mocks/schemas/{schema_file}").read_text()))

    # Act
    result = Schema.from_avro(schema.to_avro())

    # Assert
    actual = without_physical_type(result.model_dump(mode="json", exclude_unset=True))
    expected = without_physical_type(schema.model_dump(mode="json", exclude_unset=True))
    assert actual == expected


@pytest.mark.parametrize(
    "schema_file",
    [
        "spark_struct_with_parameterized_types.json",
        "spark_struct_with_metadata.json",
        "spark_struct_with_nested_types.json",
    ],
)
def test_spark_schema_should_be_written_back_after_avro_round_trip(schema_file):
    # Arrange
    spark_schema = json.loads(Path(f"tests/mocks/schemas/{schema_file}").read_text())
    schema = Schema.from_avro(Schema.from_spark(spark_schema).to_avro())

    # Act
    result = schema.to_spark()

    # Assert
    actual = result
    expected = {**spark_schema, "metadata": {}}
    assert actual == expected


def test_spark_schema_should_become_avro_with_nullable_fields_as_null_unions():
    # Arrange
    schema = Schema.from_spark(
        {
            "type": "struct",
            "fields": [
                {"name": "email", "type": "string", "nullable": True, "metadata": {}},
                {"name": "id", "type": "long", "nullable": False, "metadata": {}},
            ],
        }
    )

    # Act
    result = schema.to_avro()

    # Assert
    actual = result
    expected = {
        "type": "record",
        "name": "root",
        "fields": [
            {"name": "email", "type": ["null", "string"], "default": None},
            {"name": "id", "type": "long"},
        ],
        "odcs": {"name": None},
    }
    assert actual == expected


def test_spark_schema_read_from_avro_should_keep_nullability():
    # Arrange
    avro_schema = {
        "type": "record",
        "name": "root",
        "fields": [
            {"name": "email", "type": ["null", "string"], "default": None},
            {"name": "id", "type": "long"},
        ],
        "odcs": {"name": None},
    }

    # Act
    result = Schema.from_avro(avro_schema)

    # Assert
    actual = result.model_dump(mode="json", exclude_unset=True)
    expected = {
        "properties": [
            {"name": "email", "logicalType": "string", "physicalType": '["null", "string"]'},
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


def test_spark_schema_should_be_written_back_with_empty_metadata_after_avro_hop():
    # Arrange
    spark_schema = {
        "type": "struct",
        "fields": [
            {"name": "email", "type": "string", "nullable": True, "metadata": {}},
            {"name": "id", "type": "long", "nullable": False, "metadata": {}},
        ],
    }
    schema = Schema.from_avro(Schema.from_spark(spark_schema).to_avro())

    # Act
    result = schema.to_spark()

    # Assert
    actual = result
    expected = {
        "type": "struct",
        "fields": [
            {"name": "email", "type": "string", "nullable": True, "metadata": {}},
            {"name": "id", "type": "long", "nullable": False, "metadata": {}},
        ],
        "metadata": {},
    }
    assert actual == expected
