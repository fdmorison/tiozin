import pytest

from tiozin.exceptions import SecretError, SecretNotFoundError


def test_secret_not_found_error_should_format_identifier_in_message():
    # Arrange
    identifier = "DB_PASSWORD"

    # Act
    error = SecretNotFoundError(identifier)

    # Assert
    actual = error.message
    expected = "Secret 'DB_PASSWORD' not found."
    assert actual == expected


def test_secret_not_found_error_raise_if_should_raise_when_condition_is_true():
    with pytest.raises(SecretNotFoundError, match="MISSING_VAR"):
        SecretNotFoundError.raise_if(True, "MISSING_VAR")


@pytest.mark.parametrize(
    "error",
    [
        SecretNotFoundError("x"),
    ],
)
def test_secret_errors_should_be_catchable_as_secret_error(error):
    with pytest.raises(SecretError):
        raise error
