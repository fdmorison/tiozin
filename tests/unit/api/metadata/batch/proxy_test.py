from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, call, patch

from tiozin.api.metadata.batch.proxy import BatchRegistryProxy

NOW = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
SINCE = datetime(2026, 1, 1, tzinfo=UTC)


# ============================================================================
# get_history - default resolution
# ============================================================================
@patch("tiozin.api.metadata.batch.proxy.utcnow")
def test_get_history_should_delegate_with_resolved_defaults(utcnow: MagicMock):
    # Arrange
    utcnow.return_value = NOW
    registry = MagicMock()
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.get_history()

    # Assert
    actual = registry.get_history.call_args
    expected = call(100, NOW - timedelta(days=7))
    assert actual == expected


def test_get_history_should_return_registry_result():
    # Arrange
    registry = MagicMock()
    proxy = BatchRegistryProxy(registry)

    # Act
    result = proxy.get_history()

    # Assert
    actual = result
    expected = registry.get_history.return_value
    assert actual == expected


@patch("tiozin.api.metadata.batch.proxy.utcnow")
def test_get_history_should_override_default_limit_when_provided(utcnow: MagicMock):
    # Arrange
    utcnow.return_value = NOW
    registry = MagicMock()
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.get_history(limit=5)

    # Assert
    actual = registry.get_history.call_args
    expected = call(5, NOW - timedelta(days=7))
    assert actual == expected


def test_get_history_should_override_default_since_when_provided():
    # Arrange
    registry = MagicMock()
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.get_history(since=SINCE)

    # Assert
    actual = registry.get_history.call_args
    expected = call(100, SINCE)
    assert actual == expected


def test_get_history_should_forward_resource_to_registry():
    # Arrange
    registry = MagicMock()
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.get_history(limit=5, since=SINCE, model="orders")

    # Assert
    actual = registry.get_history.call_args
    expected = call(5, SINCE, model="orders")
    assert actual == expected
