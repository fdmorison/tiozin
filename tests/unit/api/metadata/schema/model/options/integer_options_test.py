import pytest

from tiozin.api.metadata.schema.model import IntegerFormat, IntegerOptions


def test_integer_options_should_default_to_spec_values():
    # Act
    result = IntegerOptions()

    # Assert
    actual = result.model_dump()
    expected = {
        "format": "i32",
        "multipleOf": None,
        "minimum": None,
        "exclusiveMinimum": None,
        "maximum": None,
        "exclusiveMaximum": None,
    }
    assert actual == expected


@pytest.mark.parametrize("format", ["i32", IntegerFormat.INT32])
def test_integer_options_should_parse_format(format):
    # Act
    result = IntegerOptions(format=format)

    # Assert
    actual = result.format
    expected = IntegerFormat.INT32
    assert actual == expected
