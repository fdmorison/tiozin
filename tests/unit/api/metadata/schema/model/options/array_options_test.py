from tiozin.api.metadata.schema.model import ArrayOptions


def test_array_options_should_default_to_spec_values():
    # Act
    result = ArrayOptions()

    # Assert
    actual = result.model_dump()
    expected = {
        "minItems": 0,
        "maxItems": None,
        "uniqueItems": False,
    }
    assert actual == expected
