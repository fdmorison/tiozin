from unittest.mock import MagicMock, patch

import pytest

from tiozin.api import Loggable


class DummyLoggable(Loggable):
    """Test class without name attribute."""

    pass


class NamedLoggable(Loggable):
    """Test class with name attribute."""

    def __init__(self, name: str):
        self.name = name


# ============================================================================
# Testing Logger Initialization
# ============================================================================
@patch("tiozin.api.loggable.logs.get_logger")
def test_logger_should_use_class_name_by_default(get_logger: MagicMock):
    # Arrange
    instance = DummyLoggable()

    # Act
    _ = instance.logger

    # Assert
    get_logger.assert_called_once_with("DummyLoggable")


@patch("tiozin.api.loggable.logs.get_logger")
def test_logger_should_use_name_attribute_when_provided(get_logger: MagicMock):
    # Arrange
    instance = NamedLoggable(name="my_custom_name")

    # Act
    _ = instance.logger

    # Assert
    get_logger.assert_called_once_with("my_custom_name")


@patch("tiozin.api.loggable.logs.get_logger")
def test_logger_should_be_cached_when_accessed_multiple_times(_get_logger: MagicMock):
    # Arrange
    instance = DummyLoggable()

    # Act
    logger1 = instance.logger
    logger2 = instance.logger

    # Assert
    assert logger1 is logger2


# ============================================================================
# Testing Log Methods
# ============================================================================
@pytest.mark.parametrize("method", ["debug", "info", "warning", "error", "exception", "critical"])
@patch("tiozin.api.loggable.config")
@patch("tiozin.api.loggable.logs.get_logger")
def test_log_method_should_delegate_to_logger(
    get_logger: MagicMock, config: MagicMock, method: str
):
    # Arrange
    config.log_json = True
    instance = NamedLoggable(name="test")

    # Act
    getattr(instance, method)("test message")

    # Assert
    getattr(get_logger.return_value, method).assert_called_once()


# ============================================================================
# Testing Message Formatting
# ============================================================================
@patch("tiozin.api.loggable.config")
def test_fmt_should_return_plain_message_for_json_logging(config: MagicMock):
    # Arrange
    config.log_json = True
    instance = NamedLoggable(name="test")

    # Act
    result = instance._fmt("hello world")

    # Assert
    actual = result
    expected = "hello world"
    assert actual == expected


@patch("tiozin.api.loggable.config")
@patch("tiozin.api.loggable.logs.get_logger")
def test_fmt_should_return_formatted_message_by_default(_get_logger: MagicMock, config: MagicMock):
    # Arrange
    config.log_json = False
    instance = NamedLoggable(name="test")
    _ = instance.logger  # lazy initialize _logger_name

    # Act
    result = instance._fmt("hello world")

    # Assert
    actual = ("test" in result, "hello world" in result, result.startswith("["))
    expected = (True, True, True)
    assert actual == expected
