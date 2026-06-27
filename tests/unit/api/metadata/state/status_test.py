import pytest

from tiozin.api.metadata.state.exceptions import StateTransitionError
from tiozin.api.metadata.state.status import StateStatus

VALID_TRANSITIONS = [
    (StateStatus.PENDING, StateStatus.RUNNING),
    (StateStatus.PENDING, StateStatus.CANCELED),
    (StateStatus.PENDING, StateStatus.PENDING),
    (StateStatus.RUNNING, StateStatus.SUCCEEDED),
    (StateStatus.RUNNING, StateStatus.FAILED),
    (StateStatus.RUNNING, StateStatus.QUARANTINED),
    (StateStatus.RUNNING, StateStatus.RUNNING),
    (StateStatus.FAILED, StateStatus.RUNNING),
    (StateStatus.FAILED, StateStatus.QUARANTINED),
    (StateStatus.FAILED, StateStatus.FAILED),
    (StateStatus.SUCCEEDED, StateStatus.PENDING),
    (StateStatus.SUCCEEDED, StateStatus.SUCCEEDED),
    (StateStatus.CANCELED, StateStatus.PENDING),
    (StateStatus.CANCELED, StateStatus.CANCELED),
    (StateStatus.QUARANTINED, StateStatus.PENDING),
    (StateStatus.QUARANTINED, StateStatus.QUARANTINED),
]

INVALID_TRANSITIONS = [
    (StateStatus.PENDING, StateStatus.SUCCEEDED),
    (StateStatus.PENDING, StateStatus.FAILED),
    (StateStatus.PENDING, StateStatus.QUARANTINED),
    (StateStatus.RUNNING, StateStatus.PENDING),
    (StateStatus.RUNNING, StateStatus.CANCELED),
    (StateStatus.SUCCEEDED, StateStatus.RUNNING),
    (StateStatus.SUCCEEDED, StateStatus.FAILED),
    (StateStatus.SUCCEEDED, StateStatus.CANCELED),
    (StateStatus.SUCCEEDED, StateStatus.QUARANTINED),
    (StateStatus.FAILED, StateStatus.PENDING),
    (StateStatus.FAILED, StateStatus.SUCCEEDED),
    (StateStatus.FAILED, StateStatus.CANCELED),
    (StateStatus.CANCELED, StateStatus.RUNNING),
    (StateStatus.CANCELED, StateStatus.SUCCEEDED),
    (StateStatus.CANCELED, StateStatus.FAILED),
    (StateStatus.CANCELED, StateStatus.QUARANTINED),
    (StateStatus.QUARANTINED, StateStatus.RUNNING),
    (StateStatus.QUARANTINED, StateStatus.SUCCEEDED),
    (StateStatus.QUARANTINED, StateStatus.FAILED),
    (StateStatus.QUARANTINED, StateStatus.CANCELED),
]

TERMINAL_STATUSES = [StateStatus.SUCCEEDED, StateStatus.CANCELED, StateStatus.QUARANTINED]
NON_TERMINAL_STATUSES = [StateStatus.PENDING, StateStatus.RUNNING, StateStatus.FAILED]

RETRIABLE_STATUSES = [StateStatus.PENDING, StateStatus.FAILED]
NON_RETRIABLE_STATUSES = [
    StateStatus.RUNNING,
    StateStatus.SUCCEEDED,
    StateStatus.CANCELED,
    StateStatus.QUARANTINED,
]

STATUS_VALUES = [
    (StateStatus.PENDING, "pending"),
    (StateStatus.RUNNING, "running"),
    (StateStatus.SUCCEEDED, "succeeded"),
    (StateStatus.FAILED, "failed"),
    (StateStatus.CANCELED, "canceled"),
    (StateStatus.QUARANTINED, "quarantined"),
]


# ============================================================================
# transition_to
# ============================================================================
@pytest.mark.parametrize("source, target", VALID_TRANSITIONS)
def test_transition_to_should_return_target_when_transition_is_valid(
    source: StateStatus,
    target: StateStatus,
):
    # Act
    actual = source.transition_to(target)

    # Assert
    expected = target
    assert actual == expected


@pytest.mark.parametrize("source, target", INVALID_TRANSITIONS)
def test_transition_to_should_raise_transition_error_when_transition_is_invalid(
    source: StateStatus,
    target: StateStatus,
):
    # Act / Assert
    with pytest.raises(StateTransitionError):
        source.transition_to(target)


@pytest.mark.parametrize("source, target", INVALID_TRANSITIONS)
def test_transition_to_should_return_source_when_invalid_and_failfast_disabled(
    source: StateStatus,
    target: StateStatus,
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
    source: StateStatus,
    target: StateStatus,
):
    # Act
    actual = source.can_transition_to(target)

    # Assert
    assert actual is True


@pytest.mark.parametrize("source, target", INVALID_TRANSITIONS)
def test_can_transition_to_should_not_pass_when_transition_is_invalid(
    source: StateStatus,
    target: StateStatus,
):
    # Act
    actual = source.can_transition_to(target)

    # Assert
    assert actual is False


# ============================================================================
# is_terminal
# ============================================================================
@pytest.mark.parametrize("status", TERMINAL_STATUSES)
def test_is_terminal_should_pass_when_status_can_only_be_replayed(status: StateStatus):
    # Act
    actual = status.is_terminal

    # Assert
    assert actual is True


@pytest.mark.parametrize("status", NON_TERMINAL_STATUSES)
def test_is_terminal_should_not_pass_when_status_can_still_progress(status: StateStatus):
    # Act
    actual = status.is_terminal

    # Assert
    assert actual is False


# ============================================================================
# is_retriable
# ============================================================================
@pytest.mark.parametrize("status", RETRIABLE_STATUSES)
def test_is_retriable_should_pass_when_status_can_transition_back_to_running(
    status: StateStatus,
):
    # Act
    actual = status.is_retriable

    # Assert
    assert actual is True


@pytest.mark.parametrize("status", NON_RETRIABLE_STATUSES)
def test_is_retriable_should_not_pass_when_status_cannot_transition_back_to_running(
    status: StateStatus,
):
    # Act
    actual = status.is_retriable

    # Assert
    assert actual is False


# ============================================================================
# is_pending / is_running / is_succeeded / is_failed / is_canceled / is_quarantined
# ============================================================================
def test_is_pending_should_pass_when_status_is_pending():
    # Act
    actual = StateStatus.PENDING.is_pending()

    # Assert
    assert actual is True


@pytest.mark.parametrize("status", [s for s in StateStatus if s is not StateStatus.PENDING])
def test_is_pending_should_not_pass_when_status_is_not_pending(status: StateStatus):
    # Act
    actual = status.is_pending()

    # Assert
    assert actual is False


def test_is_running_should_pass_when_status_is_running():
    # Act
    actual = StateStatus.RUNNING.is_running()

    # Assert
    assert actual is True


@pytest.mark.parametrize("status", [s for s in StateStatus if s is not StateStatus.RUNNING])
def test_is_running_should_not_pass_when_status_is_not_running(status: StateStatus):
    # Act
    actual = status.is_running()

    # Assert
    assert actual is False


def test_is_succeeded_should_pass_when_status_is_succeeded():
    # Act
    actual = StateStatus.SUCCEEDED.is_succeeded()

    # Assert
    assert actual is True


@pytest.mark.parametrize("status", [s for s in StateStatus if s is not StateStatus.SUCCEEDED])
def test_is_succeeded_should_not_pass_when_status_is_not_succeeded(status: StateStatus):
    # Act
    actual = status.is_succeeded()

    # Assert
    assert actual is False


def test_is_failed_should_pass_when_status_is_failed():
    # Act
    actual = StateStatus.FAILED.is_failed()

    # Assert
    assert actual is True


@pytest.mark.parametrize("status", [s for s in StateStatus if s is not StateStatus.FAILED])
def test_is_failed_should_not_pass_when_status_is_not_failed(status: StateStatus):
    # Act
    actual = status.is_failed()

    # Assert
    assert actual is False


def test_is_canceled_should_pass_when_status_is_canceled():
    # Act
    actual = StateStatus.CANCELED.is_canceled()

    # Assert
    assert actual is True


@pytest.mark.parametrize("status", [s for s in StateStatus if s is not StateStatus.CANCELED])
def test_is_canceled_should_not_pass_when_status_is_not_canceled(status: StateStatus):
    # Act
    actual = status.is_canceled()

    # Assert
    assert actual is False


def test_is_quarantined_should_pass_when_status_is_quarantined():
    # Act
    actual = StateStatus.QUARANTINED.is_quarantined()

    # Assert
    assert actual is True


@pytest.mark.parametrize("status", [s for s in StateStatus if s is not StateStatus.QUARANTINED])
def test_is_quarantined_should_not_pass_when_status_is_not_quarantined(status: StateStatus):
    # Act
    actual = status.is_quarantined()

    # Assert
    assert actual is False


# ============================================================================
# enum string value
# ============================================================================
@pytest.mark.parametrize("status, value", STATUS_VALUES)
def test_status_value_should_be_lowercase_name(status: StateStatus, value: str):
    # Act
    actual = status.value

    # Assert
    expected = value
    assert actual == expected


@pytest.mark.parametrize("status, value", STATUS_VALUES)
def test_status_str_should_be_lowercase_name(status: StateStatus, value: str):
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
    actual = StateStatus.SUCCEEDED.to_pending()

    # Assert
    expected = StateStatus.PENDING
    assert actual == expected


def test_to_pending_should_raise_transition_error_when_invalid():
    # Act / Assert
    with pytest.raises(StateTransitionError):
        StateStatus.RUNNING.to_pending()


# ============================================================================
# to_running
# ============================================================================
def test_to_running_should_return_running_when_valid():
    # Act
    actual = StateStatus.PENDING.to_running()

    # Assert
    expected = StateStatus.RUNNING
    assert actual == expected


def test_to_running_should_raise_transition_error_when_invalid():
    # Act / Assert
    with pytest.raises(StateTransitionError):
        StateStatus.SUCCEEDED.to_running()


# ============================================================================
# to_succeeded
# ============================================================================
def test_to_succeeded_should_return_succeeded_when_valid():
    # Act
    actual = StateStatus.RUNNING.to_succeeded()

    # Assert
    expected = StateStatus.SUCCEEDED
    assert actual == expected


def test_to_succeeded_should_raise_transition_error_when_invalid():
    # Act / Assert
    with pytest.raises(StateTransitionError):
        StateStatus.PENDING.to_succeeded()


# ============================================================================
# to_failed
# ============================================================================
def test_to_failed_should_return_failed_when_valid():
    # Act
    actual = StateStatus.RUNNING.to_failed()

    # Assert
    expected = StateStatus.FAILED
    assert actual == expected


def test_to_failed_should_raise_transition_error_when_invalid():
    # Act / Assert
    with pytest.raises(StateTransitionError):
        StateStatus.PENDING.to_failed()


# ============================================================================
# to_canceled
# ============================================================================
def test_to_canceled_should_return_canceled_when_valid():
    # Act
    actual = StateStatus.PENDING.to_canceled()

    # Assert
    expected = StateStatus.CANCELED
    assert actual == expected


def test_to_canceled_should_raise_transition_error_when_invalid():
    # Act / Assert
    with pytest.raises(StateTransitionError):
        StateStatus.RUNNING.to_canceled()


# ============================================================================
# to_quarantined
# ============================================================================
def test_to_quarantined_should_return_quarantined_when_valid():
    # Act
    actual = StateStatus.RUNNING.to_quarantined()

    # Assert
    expected = StateStatus.QUARANTINED
    assert actual == expected


def test_to_quarantined_should_raise_transition_error_when_invalid():
    # Act / Assert
    with pytest.raises(StateTransitionError):
        StateStatus.PENDING.to_quarantined()
