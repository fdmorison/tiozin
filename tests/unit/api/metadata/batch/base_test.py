from datetime import UTC, datetime
from unittest.mock import call, patch

import pytest

from tests.stubs import BatchRegistryStub
from tiozin import Batch, BatchStatus
from tiozin.api.metadata.batch.exceptions import BatchTransitionError

NOMINAL_TIME = datetime(2026, 1, 15, tzinfo=UTC)
OLD_UPDATED_AT = datetime(2026, 1, 1, tzinfo=UTC)
FIXED_NOW = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)


def any_source_of(target: BatchStatus) -> BatchStatus:
    return [source for source in BatchStatus if target in BatchStatus.__state_machine__[source]][0]


# ============================================================================
# begin
# ============================================================================
def test_begin_should_transition_status_to_running(batch_registry_stub, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=any_source_of(BatchStatus.RUNNING),
    )

    # Act
    batch_registry_stub.begin(batch)

    # Assert
    actual = batch.status
    expected = BatchStatus.RUNNING
    assert actual == expected


def test_begin_should_merge_attributes(batch_registry_stub, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=any_source_of(BatchStatus.RUNNING),
        attributes={"existing1": "value1"},
    )

    # Act
    batch_registry_stub.begin(batch, extra1="value2")

    # Assert
    actual = batch.attributes
    expected = {"existing1": "value1", "extra1": "value2"}
    assert actual == expected


@patch.object(BatchRegistryStub, "register_transition")
def test_begin_should_record_transition(register_transition, batch_registry_stub, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=any_source_of(BatchStatus.RUNNING),
    )

    # Act
    batch_registry_stub.begin(batch)

    # Assert
    register_transition.assert_called_once_with(batch)


def test_begin_should_return_recorded_batch(batch_registry_stub, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=any_source_of(BatchStatus.RUNNING),
    )

    # Act
    result = batch_registry_stub.begin(batch)

    # Assert
    assert result is batch


@patch("tiozin.api.metadata.batch.base.utcnow", return_value=FIXED_NOW)
def test_begin_should_bump_updated_at(utcnow, batch_registry_stub, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=any_source_of(BatchStatus.RUNNING),
        updated_at=OLD_UPDATED_AT,
    )

    # Act
    batch_registry_stub.begin(batch)

    # Assert
    actual = batch.updated_at
    expected = FIXED_NOW
    assert actual == expected


@patch.object(BatchRegistryStub, "register_transition")
def test_begin_should_not_record_transition_when_already_running(
    register_transition, batch_registry_stub, fake_domain
):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.RUNNING,
    )

    # Act
    batch_registry_stub.begin(batch)

    # Assert
    register_transition.assert_not_called()


def test_begin_should_keep_updated_at_when_already_running(batch_registry_stub, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.RUNNING,
        updated_at=OLD_UPDATED_AT,
    )

    # Act
    batch_registry_stub.begin(batch)

    # Assert
    actual = batch.updated_at
    expected = OLD_UPDATED_AT
    assert actual == expected


@patch.object(BatchRegistryStub, "warning")
def test_begin_should_warn_when_already_running(warning, batch_registry_stub, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.RUNNING,
    )

    # Act
    batch_registry_stub.begin(batch)

    # Assert
    actual = warning.call_args
    expected = call("Batch %s is already running, so there is nothing to begin.", batch)
    assert actual == expected


def test_begin_should_raise_transition_error_when_transition_is_invalid(
    batch_registry_stub, fake_domain
):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.SUCCEEDED,
    )

    # Act / Assert
    with pytest.raises(BatchTransitionError):
        batch_registry_stub.begin(batch)


def test_begin_should_keep_status_when_transition_is_invalid_and_failfast_disabled(fake_domain):
    # Arrange
    registry = BatchRegistryStub(failfast=False)
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.SUCCEEDED,
    )

    # Act
    registry.begin(batch)

    # Assert
    actual = batch.status
    expected = BatchStatus.SUCCEEDED
    assert actual == expected


# ============================================================================
# commit
# ============================================================================
def test_commit_should_transition_status_to_succeeded(batch_registry_stub, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=any_source_of(
            BatchStatus.SUCCEEDED,
        ),
    )

    # Act
    batch_registry_stub.commit(batch)

    # Assert
    actual = batch.status
    expected = BatchStatus.SUCCEEDED
    assert actual == expected


def test_commit_should_merge_attributes(batch_registry_stub, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=any_source_of(BatchStatus.SUCCEEDED),
        attributes={"existing1": "value1"},
    )

    # Act
    batch_registry_stub.commit(batch, extra1="value2")

    # Assert
    actual = batch.attributes
    expected = {"existing1": "value1", "extra1": "value2"}
    assert actual == expected


@patch.object(BatchRegistryStub, "register_transition")
def test_commit_should_record_transition(register_transition, batch_registry_stub, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=any_source_of(BatchStatus.SUCCEEDED),
    )

    # Act
    batch_registry_stub.commit(batch)

    # Assert
    register_transition.assert_called_once_with(batch)


@patch.object(BatchRegistryStub, "register_transition")
def test_commit_should_not_record_transition_when_already_succeeded(
    register_transition, batch_registry_stub, fake_domain
):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.SUCCEEDED,
    )

    # Act
    batch_registry_stub.commit(batch)

    # Assert
    register_transition.assert_not_called()


# ============================================================================
# fail
# ============================================================================
def test_fail_should_transition_status_to_failed(batch_registry_stub, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=any_source_of(
            BatchStatus.FAILED,
        ),
    )

    # Act
    batch_registry_stub.fail(batch)

    # Assert
    actual = batch.status
    expected = BatchStatus.FAILED
    assert actual == expected


def test_fail_should_increment_failure_count(batch_registry_stub, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=any_source_of(BatchStatus.FAILED),
    )

    # Act
    batch_registry_stub.fail(batch)

    # Assert
    actual = batch.failure_count
    expected = 1
    assert actual == expected


def test_fail_should_merge_attributes(batch_registry_stub, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=any_source_of(BatchStatus.FAILED),
        attributes={"existing1": "value1"},
    )

    # Act
    batch_registry_stub.fail(batch, extra1="value2")

    # Assert
    actual = batch.attributes
    expected = {"existing1": "value1", "extra1": "value2"}
    assert actual == expected


@patch.object(BatchRegistryStub, "register_transition")
def test_fail_should_record_transition(register_transition, batch_registry_stub, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=any_source_of(BatchStatus.FAILED),
    )

    # Act
    batch_registry_stub.fail(batch)

    # Assert
    register_transition.assert_called_once_with(batch)


@patch.object(BatchRegistryStub, "register_transition")
def test_fail_should_not_record_transition_when_already_failed(
    register_transition, batch_registry_stub, fake_domain
):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.FAILED,
    )

    # Act
    batch_registry_stub.fail(batch)

    # Assert
    register_transition.assert_not_called()


@pytest.mark.parametrize(
    "failure_count, expected_status",
    [
        (0, BatchStatus.FAILED),
        (2, BatchStatus.FAILED),
        (3, BatchStatus.QUARANTINED),
    ],
)
def test_fail_should_escalate_to_quarantine_when_failure_count_exceeds_retries(
    failure_count, expected_status, batch_registry_stub, fake_domain
):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=any_source_of(BatchStatus.FAILED),
        failure_count=failure_count,
    )

    # Act
    batch_registry_stub.fail(batch)

    # Assert
    actual = batch.status
    expected = expected_status
    assert actual == expected


def test_fail_should_escalate_to_quarantine_when_retries_is_exhausted(fake_domain):
    # Arrange
    registry = BatchRegistryStub(retries=1)
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=any_source_of(BatchStatus.FAILED),
        failure_count=1,
    )

    # Act
    registry.fail(batch)

    # Assert
    actual = batch.status
    expected = BatchStatus.QUARANTINED
    assert actual == expected


# ============================================================================
# cancel
# ============================================================================
def test_cancel_should_transition_status_to_canceled(batch_registry_stub, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=any_source_of(BatchStatus.CANCELED),
    )

    # Act
    batch_registry_stub.cancel(batch)

    # Assert
    actual = batch.status
    expected = BatchStatus.CANCELED
    assert actual == expected


def test_cancel_should_merge_attributes(batch_registry_stub, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=any_source_of(BatchStatus.CANCELED),
        attributes={"existing1": "value1"},
    )

    # Act
    batch_registry_stub.cancel(batch, extra1="value2")

    # Assert
    actual = batch.attributes
    expected = {"existing1": "value1", "extra1": "value2"}
    assert actual == expected


@patch.object(BatchRegistryStub, "register_transition")
def test_cancel_should_record_transition(register_transition, batch_registry_stub, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=any_source_of(BatchStatus.CANCELED),
    )

    # Act
    batch_registry_stub.cancel(batch)

    # Assert
    register_transition.assert_called_once_with(batch)


@patch.object(BatchRegistryStub, "register_transition")
def test_cancel_should_not_record_transition_when_already_canceled(
    register_transition, batch_registry_stub, fake_domain
):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.CANCELED,
    )

    # Act
    batch_registry_stub.cancel(batch)

    # Assert
    register_transition.assert_not_called()


# ============================================================================
# quarantine
# ============================================================================
def test_quarantine_should_transition_status_to_quarantined(batch_registry_stub, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.RUNNING,
    )

    # Act
    batch_registry_stub.quarantine(batch)

    # Assert
    actual = batch.status
    expected = BatchStatus.QUARANTINED
    assert actual == expected


def test_quarantine_should_merge_attributes(batch_registry_stub, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.RUNNING,
        attributes={"existing1": "value1"},
    )

    # Act
    batch_registry_stub.quarantine(batch, extra1="value2")

    # Assert
    actual = batch.attributes
    expected = {"existing1": "value1", "extra1": "value2"}
    assert actual == expected


@patch.object(BatchRegistryStub, "register_transition")
def test_quarantine_should_record_transition(register_transition, batch_registry_stub, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.RUNNING,
    )

    # Act
    batch_registry_stub.quarantine(batch)

    # Assert
    register_transition.assert_called_once_with(batch)


@patch.object(BatchRegistryStub, "register_transition")
def test_quarantine_should_not_record_transition_when_already_quarantined(
    register_transition, batch_registry_stub, fake_domain
):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.QUARANTINED,
    )

    # Act
    batch_registry_stub.quarantine(batch)

    # Assert
    register_transition.assert_not_called()


# ============================================================================
# replay
# ============================================================================
def test_replay_should_transition_status_to_pending(batch_registry_stub, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.SUCCEEDED,
    )

    # Act
    batch_registry_stub.replay(batch)

    # Assert
    actual = batch.status
    expected = BatchStatus.PENDING
    assert actual == expected


def test_replay_should_reset_failure_count(batch_registry_stub, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.QUARANTINED,
        failure_count=3,
    )

    # Act
    batch_registry_stub.replay(batch)

    # Assert
    actual = batch.failure_count
    expected = 0
    assert actual == expected


def test_replay_should_merge_attributes(batch_registry_stub, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.SUCCEEDED,
        attributes={"existing1": "value1"},
    )

    # Act
    batch_registry_stub.replay(batch, extra1="value2")

    # Assert
    actual = batch.attributes
    expected = {"existing1": "value1", "extra1": "value2"}
    assert actual == expected


@patch.object(BatchRegistryStub, "register_transition")
def test_replay_should_record_transition(register_transition, batch_registry_stub, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.SUCCEEDED,
    )

    # Act
    batch_registry_stub.replay(batch)

    # Assert
    register_transition.assert_called_once_with(batch)


@patch.object(BatchRegistryStub, "register_transition")
def test_replay_should_not_record_transition_when_already_pending(
    register_transition, batch_registry_stub, fake_domain
):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.PENDING,
    )

    # Act
    batch_registry_stub.replay(batch)

    # Assert
    register_transition.assert_not_called()
