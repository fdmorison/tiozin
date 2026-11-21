from tiozin.api.metadata.schema.model import NumberOptions


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
