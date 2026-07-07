from tiozin import Secret
from tiozin.api.metadata.secret.model import MASK

# ============================================================================
# Secret — construction
# ============================================================================


def test_secret_should_expose_value_as_str():
    # Arrange / Act
    result = Secret("mypassword")

    # Assert
    actual = str(result)
    expected = "mypassword"
    assert actual == expected


def test_secret_should_mask_value_in_repr():
    # Arrange / Act
    result = Secret("mypassword")

    # Assert
    actual = repr(result)
    expected = MASK
    assert actual == expected


def test_secret_should_be_instance_of_str():
    # Arrange / Act
    result = Secret("mypassword")

    # Assert
    actual = isinstance(result, str)
    expected = True
    assert actual == expected


# ============================================================================
# Secret — concatenation (str + Secret)
# ============================================================================


def test_secret_should_return_secret_when_prepended_by_str():
    # Arrange
    s = Secret("mypassword")

    # Act
    result = "jdbc:postgresql://host/db?password=" + s

    # Assert
    actual = isinstance(result, Secret)
    expected = True
    assert actual == expected


def test_secret_should_preserve_full_value_when_prepended_by_str():
    # Arrange
    s = Secret("mypassword")

    # Act
    result = "prefix=" + s

    # Assert
    actual = str(result)
    expected = "prefix=mypassword"
    assert actual == expected


def test_secret_should_mask_only_sensitive_segment_when_prepended_by_str():
    # Arrange
    s = Secret("mypassword")

    # Act
    result = "prefix=" + s

    # Assert
    actual = repr(result)
    expected = f"prefix={MASK}"
    assert actual == expected


# ============================================================================
# Secret — concatenation (Secret + str)
# ============================================================================


def test_secret_should_return_secret_when_appended_by_str():
    # Arrange
    s = Secret("mypassword")

    # Act
    result = s + "@localhost"

    # Assert
    actual = isinstance(result, Secret)
    expected = True
    assert actual == expected


def test_secret_should_preserve_full_value_when_appended_by_str():
    # Arrange
    s = Secret("mypassword")

    # Act
    result = s + "@localhost"

    # Assert
    actual = str(result)
    expected = "mypassword@localhost"
    assert actual == expected


def test_secret_should_mask_only_sensitive_segment_when_appended_by_str():
    # Arrange
    s = Secret("mypassword")

    # Act
    result = s + "@localhost"

    # Assert
    actual = repr(result)
    expected = f"{MASK}@localhost"
    assert actual == expected


# ============================================================================
# Secret — concatenation (Secret + Secret)
# ============================================================================


def test_secret_should_mask_all_segments_when_two_secrets_combined():
    # Arrange
    user = Secret("admin")
    password = Secret("mypassword")

    # Act
    result = user + ":" + password

    # Assert
    actual = repr(result)
    expected = f"{MASK}:{MASK}"
    assert actual == expected


def test_secret_should_preserve_full_value_when_two_secrets_combined():
    # Arrange
    user = Secret("admin")
    password = Secret("mypassword")

    # Act
    result = user + ":" + password

    # Assert
    actual = str(result)
    expected = "admin:mypassword"
    assert actual == expected
