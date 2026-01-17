from unittest.mock import MagicMock, patch

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


def test_logger_should_not_exist_when_not_accessed():
    # Arrange
    instance = DummyLoggable()

    # Act
    # (no action - just checking initial state)

    # Assert
    assert not hasattr(instance, "_logger")


@patch("tiozin.api.loggable.logs.get_logger")
def test_logger_should_be_created_when_first_accessed(_get_logger: MagicMock):
    # Arrange
    instance = DummyLoggable()

    # Act
    _ = instance.logger

    # Assert
    assert hasattr(instance, "_logger")


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
@patch("tiozin.api.loggable.config")
@patch("tiozin.api.loggable.logs.get_logger")
def test_debug_should_delegate_to_logger(get_logger: MagicMock, config: MagicMock):
    # Arrange
    config.log_json = True
    instance = NamedLoggable(name="test")

    # Act
    instance.debug("test message")

    # Assert
    get_logger.return_value.debug.assert_called_once()


@patch("tiozin.api.loggable.config")
@patch("tiozin.api.loggable.logs.get_logger")
def test_info_should_delegate_to_logger(get_logger: MagicMock, config: MagicMock):
    # Arrange
    config.log_json = True
    instance = NamedLoggable(name="test")

    # Act
    instance.info("test message")

    # Assert
    get_logger.return_value.info.assert_called_once()


@patch("tiozin.api.loggable.config")
@patch("tiozin.api.loggable.logs.get_logger")
def test_warning_should_delegate_to_logger(get_logger: MagicMock, config: MagicMock):
    # Arrange
    config.log_json = True
    instance = NamedLoggable(name="test")

    # Act
    instance.warning("test message")

    # Assert
    get_logger.return_value.warning.assert_called_once()


@patch("tiozin.api.loggable.config")
@patch("tiozin.api.loggable.logs.get_logger")
def test_error_should_delegate_to_logger(get_logger: MagicMock, config: MagicMock):
    # Arrange
    config.log_json = True
    instance = NamedLoggable(name="test")

    # Act
    instance.error("test message")

    # Assert
    get_logger.return_value.error.assert_called_once()


@patch("tiozin.api.loggable.config")
@patch("tiozin.api.loggable.logs.get_logger")
def test_exception_should_delegate_to_logger(get_logger: MagicMock, config: MagicMock):
    # Arrange
    config.log_json = True
    instance = NamedLoggable(name="test")

    # Act
    instance.exception("test message")

    # Assert
    get_logger.return_value.exception.assert_called_once()


@patch("tiozin.api.loggable.config")
@patch("tiozin.api.loggable.logs.get_logger")
def test_critical_should_delegate_to_logger(get_logger: MagicMock, config: MagicMock):
    # Arrange
    config.log_json = True
    instance = NamedLoggable(name="test")

    # Act
    instance.critical("test message")

    # Assert
    get_logger.return_value.critical.assert_called_once()


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
    assert result == "hello world"


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
    assert "test" in result
    assert "hello world" in result
    assert result.startswith("[") and "]" in result
