from pathlib import Path

from tiozin import Schema
from tiozin.api.metadata.schema.model import Property
from tiozin.utils import load_yaml

_TIOZIN_SCHEMA_YAML = Path("tests/mocks/schemas/user/tiozin.odcs.yaml").read_text()


def test_model_dump_should_build_odcs_schema():
    # Arrange
    tiozin_schema = Schema.from_yaml(_TIOZIN_SCHEMA_YAML)

    # Act
    result = tiozin_schema.model_dump(mode="json", exclude_unset=True)

    # Assert
    actual = result
    expected = {
        "name": "users",
        "logicalType": "object",
        "physicalType": "table",
        "physicalName": "users",
        "description": "User data with friends and profile.",
        "properties": [
            {"name": "name", "logicalType": "string", "physicalType": "string"},
            {
                "name": "profile",
                "logicalType": "object",
                "physicalType": "record",
                "properties": [
                    {
                        "name": "age",
                        "logicalType": "integer",
                        "physicalType": "int",
                        "logicalTypeOptions": {"format": "i32"},
                    }
                ],
            },
            {
                "name": "friends",
                "logicalType": "array",
                "physicalType": "array",
                "items": {
                    "name": "items",
                    "logicalType": "object",
                    "physicalType": "record",
                    "properties": [
                        {"name": "name", "logicalType": "string", "physicalType": "string"}
                    ],
                },
            },
        ],
    }
    assert actual == expected


def test_model_validate_should_parse_odcs_schema():
    # Arrange
    odcs_schema = load_yaml(_TIOZIN_SCHEMA_YAML)

    # Act
    result = Schema.model_validate(odcs_schema)

    # Assert
    actual = result
    expected = Schema(
        name="users",
        logicalType="object",
        physicalType="table",
        physicalName="users",
        description="User data with friends and profile.",
        properties=[
            Property(name="name", logicalType="string", physicalType="string"),
            Property(
                name="profile",
                logicalType="object",
                physicalType="record",
                properties=[
                    Property(
                        name="age",
                        logicalType="integer",
                        physicalType="int",
                        logicalTypeOptions={"format": "i32"},
                    )
                ],
            ),
            Property(
                name="friends",
                logicalType="array",
                physicalType="array",
                items=Property(
                    name="items",
                    logicalType="object",
                    physicalType="record",
                    properties=[
                        Property(name="name", logicalType="string", physicalType="string"),
                    ],
                ),
            ),
        ],
    )
    assert actual == expected


def test_roundtrip_should_preserve_schema():
    # Arrange
    original = Schema.from_yaml(_TIOZIN_SCHEMA_YAML)
    odcs_schema = original.model_dump(mode="json", exclude_unset=True)

    # Act
    result = Schema.model_validate(odcs_schema)

    # Assert
    actual = result.model_dump()
    expected = original.model_dump()
    assert actual == expected
