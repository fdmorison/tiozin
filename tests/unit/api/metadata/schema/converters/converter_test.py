import pytest

from tiozin import Schema
from tiozin.api.metadata.schema.converters import SchemaConverter
from tiozin.api.metadata.schema.converters.avro import AvroSchemaConverter
from tiozin.api.metadata.schema.converters.spark import SparkSchemaConverter
from tiozin.exceptions import SchemaError


@pytest.mark.parametrize(
    "format, expected",
    [
        ("spark", SparkSchemaConverter),
        ("avro", AvroSchemaConverter),
    ],
)
def test_for_format_should_return_builtin_converter(format, expected):
    # Act
    result = SchemaConverter.for_format(format)

    # Assert
    actual = type(result)
    assert actual == expected


def test_for_format_should_return_same_converter_on_every_call():
    # Arrange
    first = SchemaConverter.for_format("spark")

    # Act
    result = SchemaConverter.for_format("spark")

    # Assert
    assert result is first


@pytest.mark.parametrize("format", ["protobuf", "odcs", "openlineage"])
def test_for_format_should_raise_schema_error_when_format_is_unsupported(format):
    # Act / Assert
    with pytest.raises(SchemaError, match="Unsupported schema format"):
        SchemaConverter.for_format(format)


def test_register_should_make_converter_available_to_schemas():
    # Arrange
    class NamesConverter(SchemaConverter[list[str]]):
        format = "test-names"

        def dump(self, schema: Schema, **options) -> list[str]:
            return list(schema.flatten())

        def load(self, schema: list[str] | str, **options) -> Schema:
            return Schema(properties=[{"name": name, "logicalType": "string"} for name in schema])

    schema = Schema(name="users").string("name").string("email")

    # Act
    SchemaConverter.register(NamesConverter())
    result = schema.to_format("test-names")

    # Assert
    actual = result
    expected = ["name", "email"]
    assert actual == expected
