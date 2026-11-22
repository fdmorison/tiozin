import json
from pathlib import Path

import pytest

from tiozin import Schema
from tiozin.api.metadata.schema.converters.spark import SparkSchemaConverter
from tiozin.api.metadata.schema.model import Map, Property


def test_load_should_accept_json_string():
    # Arrange
    spark_schema = json.dumps(
        {
            "type": "struct",
            "fields": [{"name": "id", "type": "long", "nullable": True, "metadata": {}}],
        }
    )

    # Act
    result = SparkSchemaConverter().load(spark_schema)

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


def test_load_should_restore_dumped_schema():
    # Arrange
    schema = Schema(
        name="users",
        properties=[
            Property(name="id", logicalType="integer", physicalType="bigint", required=True),
            Property(name="starts_at", logicalType="time", physicalType="string", required=False),
            Property(
                name="email",
                logicalType="string",
                physicalType="string",
                description="Email address",
                classification="pii",
                customProperties=[
                    {"property": "source", "value": "crm", "description": "System of record"}
                ],
            ),
            Property(
                name="scores",
                logicalType="map",
                map=Map(
                    key=Property(logicalType="string", physicalType="string", required=True),
                    value=Property(logicalType="integer", physicalType="long", required=True),
                ),
            ),
        ],
    )

    # Act
    result = SparkSchemaConverter().load(SparkSchemaConverter().dump(schema, version="4.1"))

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
            },
            {
                "name": "starts_at",
                "logicalType": "time",
                "physicalType": "time(6)",
                "required": False,
                "customProperties": [{"property": "timeUnit", "value": "micros"}],
            },
            {
                "name": "email",
                "logicalType": "string",
                "physicalType": "string",
                "description": "Email address",
                "classification": "pii",
                "customProperties": [
                    {"property": "source", "value": "crm", "description": "System of record"}
                ],
            },
            {
                "name": "scores",
                "logicalType": "map",
                "physicalType": (
                    '{"type": "map", "keyType": "string", "valueType": "long", '
                    '"valueContainsNull": false}'
                ),
                "map": {
                    "key": {"logicalType": "string", "physicalType": "string", "required": True},
                    "value": {
                        "logicalType": "integer",
                        "physicalType": "long",
                        "logicalTypeOptions": {"format": "i64"},
                        "required": True,
                    },
                },
            },
        ],
    }
    assert actual == expected


@pytest.mark.parametrize("version", ["3.5", "4.1"])
def test_load_should_restore_time_unit_finer_than_spark_time(version):
    # Arrange
    schema = Schema(name="users").time("starts_at", timeUnit="nanos")

    # Act
    result = SparkSchemaConverter().load(SparkSchemaConverter().dump(schema, version=version))

    # Assert
    actual = result.properties[0].timeUnit
    expected = "nanos"
    assert actual == expected


@pytest.mark.parametrize(
    "schema_file",
    [
        "spark_struct_with_parameterized_types.json",
        "spark_struct_with_metadata.json",
        "spark_struct_with_nested_types.json",
    ],
)
def test_load_should_round_trip_spark_schema(schema_file):
    # Arrange
    spark_schema = json.loads(Path(f"tests/mocks/schemas/{schema_file}").read_text())

    # Act
    result = SparkSchemaConverter().dump(SparkSchemaConverter().load(spark_schema))

    # Assert
    actual = result
    expected = {**spark_schema, "metadata": {}}
    assert actual == expected


def test_dump_should_write_time_as_timestamp_ntz_when_target_version_has_no_time_type():
    # Arrange
    schema = Schema(name="users").time("starts_at")

    # Act
    result = SparkSchemaConverter().dump(schema, version="3.5")

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


def test_dump_should_ignore_unknown_options():
    # Arrange
    schema = Schema(name="users").integer("id")

    # Act
    result = SparkSchemaConverter().dump(schema, version="4.1", compression="zstd")

    # Assert
    actual = result
    expected = {
        "type": "struct",
        "fields": [{"name": "id", "type": "long", "nullable": True, "metadata": {}}],
        "metadata": {"name": "users"},
    }
    assert actual == expected


def test_load_should_ignore_unknown_options():
    # Arrange
    spark_schema = {
        "type": "struct",
        "fields": [{"name": "id", "type": "long", "nullable": True, "metadata": {}}],
    }

    # Act
    result = SparkSchemaConverter().load(spark_schema, compression="zstd")

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
