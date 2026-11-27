import pytest

from tiozin.api.metadata.schema.model import NumberFormat, NumberOptions


def test_number_options_should_default_to_spec_values():
    # Act
    result = NumberOptions()

    # Assert
    actual = result.model_dump()
    expected = {
        "format": None,
        "multipleOf": None,
        "minimum": None,
        "exclusiveMinimum": None,
        "maximum": None,
        "exclusiveMaximum": None,
    }
    assert actual == expected


@pytest.mark.parametrize("format", ["f32", NumberFormat.FLOAT32])
def test_number_options_should_parse_format(format):
    # Act
    result = NumberOptions(format=format)

    # Assert
    actual = result.format
    expected = NumberFormat.FLOAT32
    assert actual == expected
