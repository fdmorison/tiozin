from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from tiozin.api.metadata.batch.exceptions import BatchTransitionError
from tiozin.api.metadata.batch.model import Batch
from tiozin.api.metadata.batch.proxy import BatchRegistryProxy
from tiozin.api.metadata.batch.status import BatchStatus


@pytest.fixture
def registry() -> MagicMock:
    mock = MagicMock()
    mock.failfast = True
    mock.retries = 3
    return mock


@pytest.fixture
def lenient_registry() -> MagicMock:
    mock = MagicMock()
    mock.failfast = False
    mock.retries = 3
    return mock


@pytest.fixture
def state(fake_domain) -> Batch:
    return Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))


# ============================================================================
# begin
# ============================================================================
def test_begin_should_transition_status_to_running(registry, state):
    # Arrange
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.begin(state)

    # Assert
    actual = state.status
    expected = BatchStatus.RUNNING
    assert actual == expected


def test_begin_should_delegate_to_registry(registry, state):
    # Arrange
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.begin(state)

    # Assert
    registry.begin.assert_called_once_with(state)


def test_begin_should_return_registry_result(registry, state):
    # Arrange
    proxy = BatchRegistryProxy(registry)

    # Act
    actual = proxy.begin(state)

    # Assert
    expected = registry.begin.return_value
    assert actual == expected


def test_begin_should_warn_when_batch_is_already_running(registry, state):
    # Arrange
    state.status = BatchStatus.RUNNING
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.begin(state)

    # Assert
    registry.warning.assert_called_once()


def test_begin_should_not_warn_when_batch_is_not_running(registry, state):
    # Arrange
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.begin(state)

    # Assert
    registry.warning.assert_not_called()


def test_begin_should_raise_transition_error_when_transition_is_invalid(registry, state):
    # Arrange
    state.status = BatchStatus.SUCCEEDED
    proxy = BatchRegistryProxy(registry)

    # Act / Assert
    with pytest.raises(BatchTransitionError):
        proxy.begin(state)


def test_begin_should_keep_status_when_invalid_and_failfast_disabled(lenient_registry, state):
    # Arrange
    state.status = BatchStatus.SUCCEEDED
    proxy = BatchRegistryProxy(lenient_registry)

    # Act
    proxy.begin(state)

    # Assert
    actual = state.status
    expected = BatchStatus.SUCCEEDED
    assert actual == expected


# ============================================================================
# commit
# ============================================================================
def test_commit_should_transition_status_to_succeeded(registry, state):
    # Arrange
    state.status = BatchStatus.RUNNING
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.commit(state)

    # Assert
    actual = state.status
    expected = BatchStatus.SUCCEEDED
    assert actual == expected


def test_commit_should_delegate_to_registry(registry, state):
    # Arrange
    state.status = BatchStatus.RUNNING
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.commit(state)

    # Assert
    registry.commit.assert_called_once_with(state)


def test_commit_should_return_registry_result(registry, state):
    # Arrange
    state.status = BatchStatus.RUNNING
    proxy = BatchRegistryProxy(registry)

    # Act
    actual = proxy.commit(state)

    # Assert
    expected = registry.commit.return_value
    assert actual == expected


def test_commit_should_warn_when_batch_is_already_succeeded(registry, state):
    # Arrange
    state.status = BatchStatus.SUCCEEDED
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.commit(state)

    # Assert
    registry.warning.assert_called_once()


def test_commit_should_not_warn_when_batch_is_not_succeeded(registry, state):
    # Arrange
    state.status = BatchStatus.RUNNING
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.commit(state)

    # Assert
    registry.warning.assert_not_called()


def test_commit_should_raise_transition_error_when_transition_is_invalid(registry, state):
    # Arrange
    proxy = BatchRegistryProxy(registry)

    # Act / Assert
    with pytest.raises(BatchTransitionError):
        proxy.commit(state)


def test_commit_should_keep_status_when_invalid_and_failfast_disabled(lenient_registry, state):
    # Arrange
    proxy = BatchRegistryProxy(lenient_registry)

    # Act
    proxy.commit(state)

    # Assert
    actual = state.status
    expected = BatchStatus.PENDING
    assert actual == expected


# ============================================================================
# fail
# ============================================================================
def test_fail_should_transition_status_to_failed(registry, state):
    # Arrange
    state.status = BatchStatus.RUNNING
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.fail(state)

    # Assert
    actual = state.status
    expected = BatchStatus.FAILED
    assert actual == expected


def test_fail_should_delegate_to_registry(registry, state):
    # Arrange
    state.status = BatchStatus.RUNNING
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.fail(state)

    # Assert
    registry.fail.assert_called_once_with(state)


def test_fail_should_return_registry_result(registry, state):
    # Arrange
    state.status = BatchStatus.RUNNING
    proxy = BatchRegistryProxy(registry)

    # Act
    actual = proxy.fail(state)

    # Assert
    expected = registry.fail.return_value
    assert actual == expected


def test_fail_should_warn_when_batch_is_already_failed(registry, state):
    # Arrange
    state.status = BatchStatus.FAILED
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.fail(state)

    # Assert
    registry.warning.assert_called_once()


def test_fail_should_not_warn_when_batch_is_not_failed(registry, state):
    # Arrange
    state.status = BatchStatus.RUNNING
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.fail(state)

    # Assert
    registry.warning.assert_not_called()


def test_fail_should_raise_transition_error_when_transition_is_invalid(registry, state):
    # Arrange
    proxy = BatchRegistryProxy(registry)

    # Act / Assert
    with pytest.raises(BatchTransitionError):
        proxy.fail(state)


def test_fail_should_keep_status_when_invalid_and_failfast_disabled(lenient_registry, state):
    # Arrange
    proxy = BatchRegistryProxy(lenient_registry)

    # Act
    proxy.fail(state)

    # Assert
    actual = state.status
    expected = BatchStatus.PENDING
    assert actual == expected


@pytest.mark.parametrize(
    "failure_count,expected_status",
    [
        (1, BatchStatus.FAILED),  # 1st try
        (2, BatchStatus.FAILED),  # 1st retry
        (3, BatchStatus.FAILED),  # 2nd retry
        (4, BatchStatus.QUARANTINED),  # 3rd retry
    ],
)
def test_fail_should_quarantine_after_maximum_retries(
    failure_count: int, expected_status: BatchStatus, registry: MagicMock, state: Batch
):
    # Arrange
    proxy = BatchRegistryProxy(registry)
    state.status = BatchStatus.RUNNING
    state.failure_count = failure_count

    # Act
    proxy.fail(state)

    # Assert
    actual = state.status
    expected = expected_status
    assert actual == expected


# ============================================================================
# cancel
# ============================================================================
def test_cancel_should_transition_status_to_canceled(registry, state):
    # Arrange
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.cancel(state)

    # Assert
    actual = state.status
    expected = BatchStatus.CANCELED
    assert actual == expected


def test_cancel_should_delegate_to_registry(registry, state):
    # Arrange
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.cancel(state)

    # Assert
    registry.cancel.assert_called_once_with(state)


def test_cancel_should_return_registry_result(registry, state):
    # Arrange
    proxy = BatchRegistryProxy(registry)

    # Act
    actual = proxy.cancel(state)

    # Assert
    expected = registry.cancel.return_value
    assert actual == expected


def test_cancel_should_warn_when_batch_is_already_canceled(registry, state):
    # Arrange
    state.status = BatchStatus.CANCELED
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.cancel(state)

    # Assert
    registry.warning.assert_called_once()


def test_cancel_should_not_warn_when_batch_is_not_canceled(registry, state):
    # Arrange
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.cancel(state)

    # Assert
    registry.warning.assert_not_called()


def test_cancel_should_raise_transition_error_when_transition_is_invalid(registry, state):
    # Arrange
    state.status = BatchStatus.RUNNING
    proxy = BatchRegistryProxy(registry)

    # Act / Assert
    with pytest.raises(BatchTransitionError):
        proxy.cancel(state)


def test_cancel_should_keep_status_when_invalid_and_failfast_disabled(lenient_registry, state):
    # Arrange
    state.status = BatchStatus.RUNNING
    proxy = BatchRegistryProxy(lenient_registry)

    # Act
    proxy.cancel(state)

    # Assert
    actual = state.status
    expected = BatchStatus.RUNNING
    assert actual == expected


# ============================================================================
# quarantine
# ============================================================================
def test_quarantine_should_transition_status_to_quarantined(registry, state):
    # Arrange
    state.status = BatchStatus.RUNNING
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.quarantine(state)

    # Assert
    actual = state.status
    expected = BatchStatus.QUARANTINED
    assert actual == expected


def test_quarantine_should_delegate_to_registry(registry, state):
    # Arrange
    state.status = BatchStatus.RUNNING
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.quarantine(state)

    # Assert
    registry.quarantine.assert_called_once_with(state)


def test_quarantine_should_return_registry_result(registry, state):
    # Arrange
    state.status = BatchStatus.RUNNING
    proxy = BatchRegistryProxy(registry)

    # Act
    actual = proxy.quarantine(state)

    # Assert
    expected = registry.quarantine.return_value
    assert actual == expected


def test_quarantine_should_warn_when_batch_is_already_quarantined(registry, state):
    # Arrange
    state.status = BatchStatus.QUARANTINED
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.quarantine(state)

    # Assert
    registry.warning.assert_called_once()


def test_quarantine_should_not_warn_when_batch_is_not_quarantined(registry, state):
    # Arrange
    state.status = BatchStatus.RUNNING
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.quarantine(state)

    # Assert
    registry.warning.assert_not_called()


def test_quarantine_should_raise_transition_error_when_transition_is_invalid(registry, state):
    # Arrange
    proxy = BatchRegistryProxy(registry)

    # Act / Assert
    with pytest.raises(BatchTransitionError):
        proxy.quarantine(state)


def test_quarantine_should_keep_status_when_invalid_and_failfast_disabled(lenient_registry, state):
    # Arrange
    proxy = BatchRegistryProxy(lenient_registry)

    # Act
    proxy.quarantine(state)

    # Assert
    actual = state.status
    expected = BatchStatus.PENDING
    assert actual == expected


# ============================================================================
# replay
# ============================================================================
def test_replay_should_transition_status_to_pending(registry, state):
    # Arrange
    state.status = BatchStatus.SUCCEEDED
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.replay(state)

    # Assert
    actual = state.status
    expected = BatchStatus.PENDING
    assert actual == expected


def test_replay_should_delegate_to_registry(registry, state):
    # Arrange
    state.status = BatchStatus.SUCCEEDED
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.replay(state)

    # Assert
    registry.replay.assert_called_once_with(state)


def test_replay_should_return_registry_result(registry, state):
    # Arrange
    state.status = BatchStatus.SUCCEEDED
    proxy = BatchRegistryProxy(registry)

    # Act
    actual = proxy.replay(state)

    # Assert
    expected = registry.replay.return_value
    assert actual == expected


def test_replay_should_warn_when_batch_is_already_pending(registry, state):
    # Arrange
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.replay(state)

    # Assert
    registry.warning.assert_called_once()


def test_replay_should_not_warn_when_batch_is_not_pending(registry, state):
    # Arrange
    state.status = BatchStatus.SUCCEEDED
    proxy = BatchRegistryProxy(registry)

    # Act
    proxy.replay(state)

    # Assert
    registry.warning.assert_not_called()


def test_replay_should_raise_transition_error_when_transition_is_invalid(registry, state):
    # Arrange
    state.status = BatchStatus.RUNNING
    proxy = BatchRegistryProxy(registry)

    # Act / Assert
    with pytest.raises(BatchTransitionError):
        proxy.replay(state)


def test_replay_should_keep_status_when_invalid_and_failfast_disabled(lenient_registry, state):
    # Arrange
    state.status = BatchStatus.RUNNING
    proxy = BatchRegistryProxy(lenient_registry)

    # Act
    proxy.replay(state)

    # Assert
    actual = state.status
    expected = BatchStatus.RUNNING
    assert actual == expected
