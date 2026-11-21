from pathlib import Path

from tests.mocks.schemas.user.spark import SPARK_SCHEMA
from tiozin import Schema

_TIOZIN_SCHEMA_YAML = Path("tests/mocks/schemas/user/tiozin.odcs.yaml").read_text()
_TIOZIN_SCHEMA_SPARK_YAML = Path("tests/mocks/schemas/user/spark.odcs.yaml").read_text()


def test_to_spark_should_build_spark_schema():
    # Arrange
    tiozin_schema = Schema.from_yaml(_TIOZIN_SCHEMA_YAML)

    # Act
    result = tiozin_schema.to_spark()

    # Assert
    actual = result
    expected = {
        "type": "struct",
        "fields": [
            {"name": "name", "type": "string", "nullable": True, "metadata": {}},
            {
                "name": "profile",
                "type": {
                    "type": "struct",
                    "fields": [
                        {"name": "age", "type": "integer", "nullable": True, "metadata": {}}
                    ],
                },
                "nullable": True,
                "metadata": {},
            },
            {
                "name": "friends",
                "type": {
                    "type": "array",
                    "elementType": {
                        "type": "struct",
                        "fields": [
                            {"name": "name", "type": "string", "nullable": True, "metadata": {}}
                        ],
                    },
                    "containsNull": True,
                },
                "nullable": True,
                "metadata": {"items": {"name": "items"}},
            },
        ],
        "metadata": {
            "name": "users",
            "logicalType": "object",
            "physicalType": "table",
            "physicalName": "users",
            "description": "User data with friends and profile.",
        },
    }
    assert actual == expected


def test_from_spark_should_parse_spark_schema():
    # Arrange
    tiozin_schema = Schema.from_yaml(_TIOZIN_SCHEMA_SPARK_YAML)

    # Act
    result = Schema.from_spark(SPARK_SCHEMA.jsonValue())

    # Assert
    actual = result.model_dump()
    expected = tiozin_schema.model_dump()
    assert actual == expected


def test_roundtrip_should_be_lossless():
    # Arrange
    original = Schema.from_spark(SPARK_SCHEMA.jsonValue())
    spark_schema = original.to_spark()

    # Act
    result = Schema.from_spark(spark_schema)

    # Assert
    actual = result.model_dump()
    expected = original.model_dump()
    assert actual == expected
