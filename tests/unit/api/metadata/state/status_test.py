import pytest

from tiozin.api.metadata.batch.exceptions import BatchTransitionError
from tiozin.api.metadata.batch.status import BatchStatus

VALID_TRANSITIONS = [
    (BatchStatus.PENDING, BatchStatus.RUNNING),
    (BatchStatus.PENDING, BatchStatus.CANCELED),
    (BatchStatus.PENDING, BatchStatus.PENDING),
    (BatchStatus.RUNNING, BatchStatus.SUCCEEDED),
    (BatchStatus.RUNNING, BatchStatus.FAILED),
    (BatchStatus.RUNNING, BatchStatus.QUARANTINED),
    (BatchStatus.RUNNING, BatchStatus.RUNNING),
    (BatchStatus.FAILED, BatchStatus.RUNNING),
    (BatchStatus.FAILED, BatchStatus.QUARANTINED),
    (BatchStatus.FAILED, BatchStatus.FAILED),
    (BatchStatus.SUCCEEDED, BatchStatus.PENDING),
    (BatchStatus.SUCCEEDED, BatchStatus.SUCCEEDED),
    (BatchStatus.CANCELED, BatchStatus.PENDING),
    (BatchStatus.CANCELED, BatchStatus.CANCELED),
    (BatchStatus.QUARANTINED, BatchStatus.PENDING),
    (BatchStatus.QUARANTINED, BatchStatus.QUARANTINED),
]

INVALID_TRANSITIONS = [
    (BatchStatus.PENDING, BatchStatus.SUCCEEDED),
    (BatchStatus.PENDING, BatchStatus.FAILED),
    (BatchStatus.PENDING, BatchStatus.QUARANTINED),
    (BatchStatus.RUNNING, BatchStatus.PENDING),
    (BatchStatus.RUNNING, BatchStatus.CANCELED),
    (BatchStatus.SUCCEEDED, BatchStatus.RUNNING),
    (BatchStatus.SUCCEEDED, BatchStatus.FAILED),
    (BatchStatus.SUCCEEDED, BatchStatus.CANCELED),
    (BatchStatus.SUCCEEDED, BatchStatus.QUARANTINED),
    (BatchStatus.FAILED, BatchStatus.PENDING),
    (BatchStatus.FAILED, BatchStatus.SUCCEEDED),
    (BatchStatus.FAILED, BatchStatus.CANCELED),
    (BatchStatus.CANCELED, BatchStatus.RUNNING),
    (BatchStatus.CANCELED, BatchStatus.SUCCEEDED),
    (BatchStatus.CANCELED, BatchStatus.FAILED),
    (BatchStatus.CANCELED, BatchStatus.QUARANTINED),
    (BatchStatus.QUARANTINED, BatchStatus.RUNNING),
    (BatchStatus.QUARANTINED, BatchStatus.SUCCEEDED),
    (BatchStatus.QUARANTINED, BatchStatus.FAILED),
    (BatchStatus.QUARANTINED, BatchStatus.CANCELED),
]

TERMINAL_STATUSES = [BatchStatus.SUCCEEDED, BatchStatus.CANCELED, BatchStatus.QUARANTINED]
NON_TERMINAL_STATUSES = [BatchStatus.PENDING, BatchStatus.RUNNING, BatchStatus.FAILED]

RETRIABLE_STATUSES = [BatchStatus.PENDING, BatchStatus.FAILED]
NON_RETRIABLE_STATUSES = [
    BatchStatus.RUNNING,
    BatchStatus.SUCCEEDED,
    BatchStatus.CANCELED,
    BatchStatus.QUARANTINED,
]

STATUS_VALUES = [
    (BatchStatus.PENDING, "pending"),
    (BatchStatus.RUNNING, "running"),
    (BatchStatus.SUCCEEDED, "succeeded"),
    (BatchStatus.FAILED, "failed"),
    (BatchStatus.CANCELED, "canceled"),
    (BatchStatus.QUARANTINED, "quarantined"),
]


# ============================================================================
# transition_to
# ============================================================================
@pytest.mark.parametrize("source, target", VALID_TRANSITIONS)
def test_transition_to_should_return_target_when_transition_is_valid(
    source: BatchStatus,
    target: BatchStatus,
):
    # Act
    actual = source.transition_to(target)

    # Assert
    expected = target
    assert actual == expected


@pytest.mark.parametrize("source, target", INVALID_TRANSITIONS)
def test_transition_to_should_raise_transition_error_when_transition_is_invalid(
    source: BatchStatus,
    target: BatchStatus,
):
    # Act / Assert
    with pytest.raises(BatchTransitionError):
        source.transition_to(target)


@pytest.mark.parametrize("source, target", INVALID_TRANSITIONS)
def test_transition_to_should_return_source_when_invalid_and_failfast_disabled(
    source: BatchStatus,
    target: BatchStatus,
):
    # Act
    actual = source.transition_to(target, failfast=False)

    # Assert
    expected = source
    assert actual == expected


# ============================================================================
# can_transition_to
# ============================================================================
@pytest.mark.parametrize("source, target", VALID_TRANSITIONS)
def test_can_transition_to_should_pass_when_transition_is_valid(
    source: BatchStatus,
    target: BatchStatus,
):
    # Act
    actual = source.can_transition_to(target)

    # Assert
    assert actual is True


@pytest.mark.parametrize("source, target", INVALID_TRANSITIONS)
def test_can_transition_to_should_not_pass_when_transition_is_invalid(
    source: BatchStatus,
    target: BatchStatus,
):
    # Act
    actual = source.can_transition_to(target)

    # Assert
    assert actual is False


# ============================================================================
# is_terminal
# ============================================================================
@pytest.mark.parametrize("status", TERMINAL_STATUSES)
def test_is_terminal_should_pass_when_status_can_only_be_replayed(status: BatchStatus):
    # Act
    actual = status.is_terminal()

    # Assert
    assert actual is True


@pytest.mark.parametrize("status", NON_TERMINAL_STATUSES)
def test_is_terminal_should_not_pass_when_status_can_still_progress(status: BatchStatus):
    # Act
    actual = status.is_terminal()

    # Assert
    assert actual is False


# ============================================================================
# is_retriable
# ============================================================================
@pytest.mark.parametrize("status", RETRIABLE_STATUSES)
def test_is_retriable_should_pass_when_status_can_transition_back_to_running(
    status: BatchStatus,
):
    # Act
    actual = status.is_retriable()

    # Assert
    assert actual is True


@pytest.mark.parametrize("status", NON_RETRIABLE_STATUSES)
def test_is_retriable_should_not_pass_when_status_cannot_transition_back_to_running(
    status: BatchStatus,
):
    # Act
    actual = status.is_retriable()

    # Assert
    assert actual is False


# ============================================================================
# is_pending / is_running / is_succeeded / is_failed / is_canceled / is_quarantined
# ============================================================================
def test_is_pending_should_pass_when_status_is_pending():
    # Act
    actual = BatchStatus.PENDING.is_pending()

    # Assert
    assert actual is True


@pytest.mark.parametrize("status", [s for s in BatchStatus if s is not BatchStatus.PENDING])
def test_is_pending_should_not_pass_when_status_is_not_pending(status: BatchStatus):
    # Act
    actual = status.is_pending()

    # Assert
    assert actual is False


def test_is_running_should_pass_when_status_is_running():
    # Act
    actual = BatchStatus.RUNNING.is_running()

    # Assert
    assert actual is True


@pytest.mark.parametrize("status", [s for s in BatchStatus if s is not BatchStatus.RUNNING])
def test_is_running_should_not_pass_when_status_is_not_running(status: BatchStatus):
    # Act
    actual = status.is_running()

    # Assert
    assert actual is False


def test_is_succeeded_should_pass_when_status_is_succeeded():
    # Act
    actual = BatchStatus.SUCCEEDED.is_succeeded()

    # Assert
    assert actual is True


@pytest.mark.parametrize("status", [s for s in BatchStatus if s is not BatchStatus.SUCCEEDED])
def test_is_succeeded_should_not_pass_when_status_is_not_succeeded(status: BatchStatus):
    # Act
    actual = status.is_succeeded()

    # Assert
    assert actual is False


def test_is_failed_should_pass_when_status_is_failed():
    # Act
    actual = BatchStatus.FAILED.is_failed()

    # Assert
    assert actual is True


@pytest.mark.parametrize("status", [s for s in BatchStatus if s is not BatchStatus.FAILED])
def test_is_failed_should_not_pass_when_status_is_not_failed(status: BatchStatus):
    # Act
    actual = status.is_failed()

    # Assert
    assert actual is False


def test_is_canceled_should_pass_when_status_is_canceled():
    # Act
    actual = BatchStatus.CANCELED.is_canceled()

    # Assert
    assert actual is True


@pytest.mark.parametrize("status", [s for s in BatchStatus if s is not BatchStatus.CANCELED])
def test_is_canceled_should_not_pass_when_status_is_not_canceled(status: BatchStatus):
    # Act
    actual = status.is_canceled()

    # Assert
    assert actual is False


def test_is_quarantined_should_pass_when_status_is_quarantined():
    # Act
    actual = BatchStatus.QUARANTINED.is_quarantined()

    # Assert
    assert actual is True


@pytest.mark.parametrize("status", [s for s in BatchStatus if s is not BatchStatus.QUARANTINED])
def test_is_quarantined_should_not_pass_when_status_is_not_quarantined(status: BatchStatus):
    # Act
    actual = status.is_quarantined()

    # Assert
    assert actual is False


# ============================================================================
# enum string value
# ============================================================================
@pytest.mark.parametrize("status, value", STATUS_VALUES)
def test_status_value_should_be_lowercase_name(status: BatchStatus, value: str):
    # Act
    actual = status.value

    # Assert
    expected = value
    assert actual == expected


@pytest.mark.parametrize("status, value", STATUS_VALUES)
def test_status_str_should_be_lowercase_name(status: BatchStatus, value: str):
    # Act
    actual = str(status)

    # Assert
    expected = value
    assert actual == expected


# ============================================================================
# to_pending
# ============================================================================
def test_to_pending_should_return_pending_when_valid():
    # Act
    actual = BatchStatus.SUCCEEDED.to_pending()

    # Assert
    expected = BatchStatus.PENDING
    assert actual == expected


def test_to_pending_should_raise_transition_error_when_invalid():
    # Act / Assert
    with pytest.raises(BatchTransitionError):
        BatchStatus.RUNNING.to_pending()


# ============================================================================
# to_running
# ============================================================================
def test_to_running_should_return_running_when_valid():
    # Act
    actual = BatchStatus.PENDING.to_running()

    # Assert
    expected = BatchStatus.RUNNING
    assert actual == expected


def test_to_running_should_raise_transition_error_when_invalid():
    # Act / Assert
    with pytest.raises(BatchTransitionError):
        BatchStatus.SUCCEEDED.to_running()


# ============================================================================
# to_succeeded
# ============================================================================
def test_to_succeeded_should_return_succeeded_when_valid():
    # Act
    actual = BatchStatus.RUNNING.to_succeeded()

    # Assert
    expected = BatchStatus.SUCCEEDED
    assert actual == expected


def test_to_succeeded_should_raise_transition_error_when_invalid():
    # Act / Assert
    with pytest.raises(BatchTransitionError):
        BatchStatus.PENDING.to_succeeded()


# ============================================================================
# to_failed
# ============================================================================
def test_to_failed_should_return_failed_when_valid():
    # Act
    actual = BatchStatus.RUNNING.to_failed()

    # Assert
    expected = BatchStatus.FAILED
    assert actual == expected


def test_to_failed_should_raise_transition_error_when_invalid():
    # Act / Assert
    with pytest.raises(BatchTransitionError):
        BatchStatus.PENDING.to_failed()


# ============================================================================
# to_canceled
# ============================================================================
def test_to_canceled_should_return_canceled_when_valid():
    # Act
    actual = BatchStatus.PENDING.to_canceled()

    # Assert
    expected = BatchStatus.CANCELED
    assert actual == expected


def test_to_canceled_should_raise_transition_error_when_invalid():
    # Act / Assert
    with pytest.raises(BatchTransitionError):
        BatchStatus.RUNNING.to_canceled()


# ============================================================================
# to_quarantined
# ============================================================================
def test_to_quarantined_should_return_quarantined_when_valid():
    # Act
    actual = BatchStatus.RUNNING.to_quarantined()

    # Assert
    expected = BatchStatus.QUARANTINED
    assert actual == expected


def test_to_quarantined_should_raise_transition_error_when_invalid():
    # Act / Assert
    with pytest.raises(BatchTransitionError):
        BatchStatus.PENDING.to_quarantined()
