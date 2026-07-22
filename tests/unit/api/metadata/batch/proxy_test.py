from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, call, patch

from freezegun import freeze_time

from tiozin import Batch
from tiozin.api.metadata.batch.proxy import BatchRegistryProxy

NOW = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
SINCE = datetime(2026, 1, 1, tzinfo=UTC)
NOMINAL_TIME = datetime(2026, 1, 15, tzinfo=UTC)

# Frozen clock and a stale timestamp for asserting register_transition stamps
# updated_at at transition time.
FROZEN_NOW = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
STALE_UPDATED_AT = datetime(2026, 1, 1, tzinfo=UTC)


# ============================================================================
# register
# ============================================================================
def test_register_should_delegate(fake_domain):
    # Arrange
    registry = MagicMock()
    proxy = BatchRegistryProxy(registry)
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    proxy.register(batch)

    # Assert
    actual = registry.register.call_args
    expected = call(batch)
    assert actual == expected


def test_register_should_preserve_result(fake_domain):
    # Arrange
    registry = MagicMock()
    proxy = BatchRegistryProxy(registry)
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    result = proxy.register(batch)

    # Assert
    actual = result
    expected = registry.register.return_value
    assert actual is expected


def test_register_should_return_batch_when_registry_returns_none(fake_domain):
    # Arrange
    registry = MagicMock()
    registry.register.return_value = None
    proxy = BatchRegistryProxy(registry)
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    result = proxy.register(batch)

    # Assert
    actual = result
    expected = batch
    assert actual is expected


def test_register_should_attach_registry_into_batch(fake_domain):
    # Arrange
    registry = MagicMock()
    registry.register.return_value = None
    proxy = BatchRegistryProxy(registry)
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    result = proxy.register(batch)

    # Assert
    actual = result._registry_ref
    expected = proxy
    assert actual is expected


def test_register_should_keep_existing_registry_reference(fake_domain):
    # Arrange
    registry = MagicMock()
    registry.register.return_value = None
    existing_registry = MagicMock()
    proxy = BatchRegistryProxy(registry)
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)
    batch._registry_ref = existing_registry

    # Act
    result = proxy.register(batch)

    # Assert
    actual = result._registry_ref
    expected = existing_registry
    assert actual is expected


# ============================================================================
# register_transition
# ============================================================================
def test_register_transition_should_delegate(fake_domain):
    # Arrange
    registry = MagicMock()
    proxy = BatchRegistryProxy(registry)
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    proxy.register_transition(batch)

    # Assert
    actual = registry.register_transition.call_args
    expected = call(batch)
    assert actual == expected


def test_register_transition_should_preserve_result(fake_domain):
    # Arrange
    registry = MagicMock()
    proxy = BatchRegistryProxy(registry)
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    result = proxy.register_transition(batch)

    # Assert
    actual = result
    expected = registry.register_transition.return_value
    assert actual is expected


def test_register_transition_should_return_batch_when_registry_returns_none(fake_domain):
    # Arrange
    registry = MagicMock()
    registry.register_transition.return_value = None
    proxy = BatchRegistryProxy(registry)
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    result = proxy.register_transition(batch)

    # Assert
    actual = result
    expected = batch
    assert actual is expected


@freeze_time(FROZEN_NOW)
def test_register_transition_should_stamp_updated_at(fake_domain):
    # Arrange
    registry = MagicMock()
    proxy = BatchRegistryProxy(registry)
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, updated_at=STALE_UPDATED_AT)

    # Act
    proxy.register_transition(batch)

    # Assert
    actual = batch.updated_at
    expected = FROZEN_NOW
    assert actual == expected


# ============================================================================
# get
# ============================================================================
def test_get_should_delegate():
    # Arrange
    registry = MagicMock()
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.get("batch-id-1", model="orders")

    # Assert
    actual = registry.get.call_args
    expected = call("batch-id-1", model="orders")
    assert actual == expected


def test_get_should_preserve_result():
    # Arrange
    registry = MagicMock()
    proxy = BatchRegistryProxy(registry)

    # Act
    result = proxy.get("batch-id-1")

    # Assert
    actual = result
    expected = registry.get.return_value
    assert actual is expected


def test_get_should_attach_registry_into_batch(fake_domain):
    # Arrange
    registry = MagicMock()
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)
    registry.get.return_value = batch
    proxy = BatchRegistryProxy(registry)

    # Act
    result = proxy.get("batch-id-1")

    # Assert
    actual = result._registry_ref
    expected = proxy
    assert actual is expected


# ============================================================================
# get_frontier
# ============================================================================
def test_get_frontier_should_delegate():
    # Arrange
    registry = MagicMock()
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.get_frontier(model="orders")

    # Assert
    actual = registry.get_frontier.call_args
    expected = call(model="orders")
    assert actual == expected


def test_get_frontier_should_preserve_result():
    # Arrange
    registry = MagicMock()
    proxy = BatchRegistryProxy(registry)

    # Act
    result = proxy.get_frontier()

    # Assert
    actual = result
    expected = registry.get_frontier.return_value
    assert actual is expected


def test_get_frontier_should_return_none_when_registry_returns_none():
    # Arrange
    registry = MagicMock()
    registry.get_frontier.return_value = None
    proxy = BatchRegistryProxy(registry)

    # Act
    result = proxy.get_frontier()

    # Assert
    assert result is None


# ============================================================================
# get_backlog
# ============================================================================
def test_get_backlog_should_delegate():
    # Arrange
    registry = MagicMock()
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.get_backlog(model="orders")

    # Assert
    actual = registry.get_backlog.call_args
    expected = call(model="orders")
    assert actual == expected


def test_get_backlog_should_preserve_result():
    # Arrange
    registry = MagicMock()
    proxy = BatchRegistryProxy(registry)

    # Act
    result = proxy.get_backlog()

    # Assert
    actual = result
    expected = registry.get_backlog.return_value
    assert actual is expected


def test_get_backlog_should_attach_registry_into_batches(fake_domain):
    # Arrange
    registry = MagicMock()
    first = Batch(**fake_domain, nominal_time=NOMINAL_TIME)
    second = Batch(**fake_domain, nominal_time=NOMINAL_TIME)
    registry.get_backlog.return_value = [first, second]
    proxy = BatchRegistryProxy(registry)

    # Act
    result = proxy.get_backlog()

    # Assert
    actual = [batch._registry_ref for batch in result]
    expected = [proxy, proxy]
    assert actual == expected


# ============================================================================
# get_board - default resolution
# ============================================================================
@patch("tiozin.api.metadata.batch.proxy.utcnow")
def test_get_board_should_delegate_with_resolved_defaults(utcnow: MagicMock):
    # Arrange
    utcnow.return_value = NOW
    registry = MagicMock()
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.get_board()

    # Assert
    actual = registry.get_board.call_args
    expected = call(100, NOW - timedelta(days=7))
    assert actual == expected


def test_get_board_should_preserve_result():
    # Arrange
    registry = MagicMock()
    proxy = BatchRegistryProxy(registry)

    # Act
    result = proxy.get_board()

    # Assert
    actual = result
    expected = registry.get_board.return_value
    assert actual == expected


@patch("tiozin.api.metadata.batch.proxy.utcnow")
def test_get_board_should_override_default_limit_when_provided(utcnow: MagicMock):
    # Arrange
    utcnow.return_value = NOW
    registry = MagicMock()
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.get_board(limit=5)

    # Assert
    actual = registry.get_board.call_args
    expected = call(5, NOW - timedelta(days=7))
    assert actual == expected


def test_get_board_should_override_default_since_when_provided():
    # Arrange
    registry = MagicMock()
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.get_board(since=SINCE)

    # Assert
    actual = registry.get_board.call_args
    expected = call(100, SINCE)
    assert actual == expected


def test_get_board_should_forward_resource():
    # Arrange
    registry = MagicMock()
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.get_board(limit=5, since=SINCE, model="orders")

    # Assert
    actual = registry.get_board.call_args
    expected = call(5, SINCE, model="orders")
    assert actual == expected
