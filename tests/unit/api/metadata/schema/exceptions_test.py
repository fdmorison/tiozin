import pytest

from tiozin.exceptions import (
    PropertyNotFoundError,
    SchemaError,
    SchemaNotFoundError,
    SchemaViolationError,
    TiozinInputError,
)


def test_schema_error_should_have_default_message():
    # Act
    error = SchemaError()

    # Assert
    actual = error.message
    expected = "The schema is invalid."
    assert actual == expected


def test_schema_error_should_be_catchable_as_tiozin_input_error():
    with pytest.raises(TiozinInputError):
        raise SchemaError()


def test_schema_violation_error_should_have_default_message():
    # Act
    error = SchemaViolationError()

    # Assert
    actual = bool(error.message)
    expected = True
    assert actual == expected


def test_schema_not_found_error_should_format_subject_in_message():
    # Arrange
    subject = "user_schema"

    # Act
    error = SchemaNotFoundError(subject=subject)

    # Assert
    actual = error.message
    expected = "Schema `user_schema` not found in the registry."
    assert actual == expected


def test_property_not_found_error_should_format_path_in_message():
    # Arrange
    path = "profile.age"

    # Act
    error = PropertyNotFoundError(path=path)

    # Assert
    actual = error.message
    expected = "Property `profile.age` not found."
    assert actual == expected


@pytest.mark.parametrize(
    "error",
    [
        SchemaNotFoundError(subject="x"),
        SchemaViolationError(),
        PropertyNotFoundError(path="x"),
    ],
)
def test_schema_errors_should_be_catchable_as_schema_error(error):
    with pytest.raises(SchemaError):
        raise error
