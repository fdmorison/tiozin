from tiozin.api.metadata.schema.model import IntegerOptions


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
