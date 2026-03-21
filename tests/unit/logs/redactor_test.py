from unittest.mock import patch

import pytest

from tiozin.logs.redactor import SecretRedactor

# ---------------------------------------------------------------------------
# add()
# ---------------------------------------------------------------------------


def test_add_should_register_secret():
    # Arrange
    redactor = SecretRedactor()

    # Act
    redactor.add("my-secret-key")

    # Assert
    actual = "my-secret-key" in redactor._known_secrets
    expected = True
    assert actual == expected


@pytest.mark.parametrize("short_value", ["", "a", "ab"])
def test_add_should_ignore_values_shorter_than_min_length(short_value):
    # Arrange
    redactor = SecretRedactor()

    # Act
    redactor.add(short_value)

    # Assert
    actual = len(redactor._known_secrets)
    expected = 0
    assert actual == expected


def test_add_should_ignore_duplicate_secrets():
    # Arrange
    redactor = SecretRedactor()
    redactor.add("my-secret-key")

    # Act
    redactor.add("my-secret-key")

    # Assert
    actual = len(redactor._known_secrets)
    expected = 1
    assert actual == expected


def test_add_should_sort_secrets_longest_first():
    # Arrange
    redactor = SecretRedactor()
    redactor.add("short")
    redactor.add("longer-secret")

    # Act
    redactor.add("medium-sec")

    # Assert
    actual = redactor._sorted_secrets
    expected = ["longer-secret", "medium-sec", "short"]
    assert actual == expected


def test_add_should_respect_custom_min_length():
    # Arrange
    redactor = SecretRedactor()

    # Act
    with patch("tiozin.logs.redactor.config.log_redact_min_length", 10):
        redactor.add("short")  # len=5, below threshold

    # Assert
    actual = len(redactor._known_secrets)
    expected = 0
    assert actual == expected


# ---------------------------------------------------------------------------
# __call__()
# ---------------------------------------------------------------------------


def test_call_should_return_event_dict_unchanged_when_no_secrets_registered():
    # Arrange
    redactor = SecretRedactor()
    event_dict = {"event": "some message", "key": "value"}

    # Act
    result = redactor(None, "info", event_dict)

    # Assert
    actual = result
    expected = {"event": "some message", "key": "value"}
    assert actual == expected


def test_call_should_redact_secret_in_string_values():
    # Arrange
    redactor = SecretRedactor()
    redactor.add("supersecret")
    event_dict = {"event": "connecting with supersecret token"}

    # Act
    result = redactor(None, "info", event_dict)

    # Assert
    actual = result["event"]
    expected = "connecting with *** token"
    assert actual == expected


def test_call_should_redact_all_occurrences_of_secret():
    # Arrange
    redactor = SecretRedactor()
    redactor.add("token123")
    event_dict = {"event": "token123 and token123"}

    # Act
    result = redactor(None, "info", event_dict)

    # Assert
    actual = result["event"]
    expected = "*** and ***"
    assert actual == expected


def test_call_should_redact_multiple_registered_secrets():
    # Arrange
    redactor = SecretRedactor()
    redactor.add("api-key-abc")
    redactor.add("password-xyz")
    event_dict = {"event": "key=api-key-abc pass=password-xyz"}

    # Act
    result = redactor(None, "info", event_dict)

    # Assert
    actual = result["event"]
    expected = "key=*** pass=***"
    assert actual == expected


def test_call_should_not_redact_non_string_values():
    # Arrange
    redactor = SecretRedactor()
    redactor.add("secret99")
    event_dict = {"event": "ok", "count": 42, "flag": True}

    # Act
    result = redactor(None, "info", event_dict)

    # Assert
    actual = (result["count"], result["flag"])
    expected = (42, True)
    assert actual == expected


def test_call_should_redact_longer_secret_before_shorter_to_avoid_partial_masking():
    # Arrange
    # If "abc" is masked before "abcdef", "abcdef" becomes "***def" instead of "***"
    redactor = SecretRedactor()
    redactor.add("abcdef")
    redactor.add("abc")
    event_dict = {"event": "value=abcdef"}

    # Act
    result = redactor(None, "info", event_dict)

    # Assert
    actual = result["event"]
    expected = "value=***"
    assert actual == expected


def test_call_should_redact_across_multiple_fields():
    # Arrange
    redactor = SecretRedactor()
    redactor.add("mysecret")
    event_dict = {"event": "msg with mysecret", "detail": "also mysecret here"}

    # Act
    result = redactor(None, "info", event_dict)

    # Assert
    actual = (result["event"], result["detail"])
    expected = ("msg with ***", "also *** here")
    assert actual == expected
