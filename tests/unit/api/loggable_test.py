from collections.abc import Callable
from unittest.mock import MagicMock, call, patch

import pytest

from tiozin.api.loggable import Loggable


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
@pytest.mark.parametrize(
    "log, expected",
    [
        (Loggable.debug, [call.debug("hello world")]),
        (Loggable.info, [call.info("hello world")]),
        (Loggable.warning, [call.warning("hello world")]),
        (Loggable.error, [call.error("hello world")]),
        (Loggable.exception, [call.exception("hello world")]),
        (Loggable.critical, [call.critical("hello world")]),
    ],
)
@patch("tiozin.api.loggable.logs.get_logger")
def test_log_method_should_delegate_to_logger(get_logger: MagicMock, log: Callable, expected: list):
    # Arrange
    instance = NamedLoggable(name="test")

    # Act
    log(instance, "hello world")

    # Assert
    actual = get_logger.return_value.method_calls
    assert actual == expected
