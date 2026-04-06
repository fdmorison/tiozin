import pytest

from tiozin.exceptions import TiozinInternalError, TiozinUsageError


def test_tiozin_error_should_have_default_attributes():
    # Act
    error = TiozinUsageError()

    # Assert
    actual = (
        bool(error.message),
        error.http_status,
        error.code,
    )
    expected = (True, 400, "TiozinUsageError")
    assert actual == expected


def test_tiozin_error_should_use_custom_attributes_when_provided():
    # Arrange
    custom_message = "Custom error message"
    custom_code = "CUSTOM_ERROR"

    # Act
    error = TiozinUsageError(message=custom_message, code=custom_code)

    # Assert
    actual = (error.message, error.code)
    expected = (custom_message, custom_code)
    assert actual == expected


def test_tiozin_error_to_dict_should_return_code_and_message():
    # Arrange
    error = TiozinUsageError(message="Test message", code="TEST_CODE")

    # Act
    result = error.to_dict()

    # Assert
    actual = result
    expected = {
        "code": "TEST_CODE",
        "message": "Test message",
        "retryable": False,
    }
    assert actual == expected


def test_tiozin_error_str_should_format_message_only():
    # Arrange
    error = TiozinUsageError(message="Test message", code="TEST_CODE")

    # Act
    result = str(error)

    # Assert
    actual = result
    expected = "Test message"
    assert actual == expected


def test_tiozin_error_raise_if_should_raise_when_condition_is_true():
    # Arrange
    condition = True
    message = "Expected to raise the error"

    # Act & Assert
    with pytest.raises(TiozinUsageError, match=message):
        TiozinUsageError.raise_if(condition, message)


def test_tiozin_unexpected_error_should_have_default_attributes():
    # Act
    error = TiozinInternalError()

    # Assert
    actual = (
        bool(error.message),
        error.http_status,
        error.code,
    )
    expected = (True, 500, "TiozinInternalError")
    assert actual == expected
