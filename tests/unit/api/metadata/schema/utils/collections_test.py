from tiozin.api.metadata.schema.utils import without_none


def test_without_none_should_drop_attributes_without_value():
    # Arrange
    attributes = {"name": "id", "description": None}

    # Act
    result = without_none(attributes)

    # Assert
    actual = result
    expected = {"name": "id"}
    assert actual == expected


def test_without_none_should_preserve_falsy_values():
    # Arrange
    attributes = {"required": False, "minimum": 0, "description": "", "tags": []}

    # Act
    result = without_none(attributes)

    # Assert
    actual = result
    expected = {"required": False, "minimum": 0, "description": "", "tags": []}
    assert actual == expected


def test_without_none_should_preserve_nested_none_values():
    # Arrange
    attributes = {"odcs": {"name": None}}

    # Act
    result = without_none(attributes)

    # Assert
    actual = result
    expected = {"odcs": {"name": None}}
    assert actual == expected
