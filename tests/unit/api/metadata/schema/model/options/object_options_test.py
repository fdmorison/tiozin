from tiozin.api.metadata.schema.model import ObjectOptions


def test_object_options_should_default_to_spec_values():
    # Act
    result = ObjectOptions()

    # Assert
    actual = result.model_dump()
    expected = {
        "minProperties": 0,
        "maxProperties": None,
        "required": None,
    }
    assert actual == expected
