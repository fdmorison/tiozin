from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from tiozin import Batch, BatchStatus
from tiozin.api.metadata.batch.state import BatchState
from tiozin.exceptions import BatchAlreadyExistsError, BatchNotFoundError
from tiozin.family.tio_kernel import IcebergBatchRegistry


@pytest.fixture()
def registry(tmp_path: Path):
    registry = IcebergBatchRegistry(location=str(tmp_path))
    registry.setup()
    yield registry
    registry.teardown()


# ============================================================================
# register
# ============================================================================
def test_register_should_persist_all_fields(registry: IcebergBatchRegistry, fake_domain: dict):
    # Arrange
    state = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 15, tzinfo=UTC),
        state=BatchState(
            start=datetime(2026, 1, 14, tzinfo=UTC),
            end=datetime(2026, 1, 15, tzinfo=UTC),
        ),
    )

    # Act
    registry.register(state)

    # Assert
    actual = registry.get_latest(**fake_domain)
    expected = state
    assert actual == expected


def test_register_should_persist_attributes(registry: IcebergBatchRegistry, fake_domain: dict):
    # Arrange
    state = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 15, tzinfo=UTC),
        attributes={"extra1": "value1", "existing1": "value2"},
    )

    # Act
    registry.register(state)

    # Assert
    actual = registry.get_latest(**fake_domain).attributes
    expected = {"extra1": "value1", "existing1": "value2"}
    assert actual == expected


def test_register_should_persist_attributes_with_none_value(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange
    state = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 15, tzinfo=UTC),
        attributes={"extra1": None},
    )

    # Act
    registry.register(state)

    # Assert
    actual = registry.get_latest(**fake_domain).attributes
    expected = {"extra1": None}
    assert actual == expected


def test_register_should_raise_when_natural_key_already_exists(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))
    registry.register(state)

    # Act / Assert
    with pytest.raises(BatchAlreadyExistsError):
        registry.register(state)


# ============================================================================
# state
# ============================================================================
def test_register_should_persist_default_start_and_watermark_as_epoch(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    registry.register(state)

    # Assert
    result = registry.get_latest(**fake_domain).state
    actual = (result.start, result.watermark)
    expected = (
        datetime(1970, 1, 1, tzinfo=UTC),
        datetime(1970, 1, 1, tzinfo=UTC),
    )
    assert actual == expected


def test_register_should_persist_default_end_as_registration_time(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange
    before = datetime.now(UTC).replace(second=0, microsecond=0)
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    registry.register(state)

    # Assert
    result = registry.get_latest(**fake_domain).state
    assert before <= result.end <= datetime.now(UTC)


def test_register_should_persist_state_window(registry: IcebergBatchRegistry, fake_domain: dict):
    # Arrange
    state = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 15, tzinfo=UTC),
        state=BatchState(
            start=datetime(2026, 1, 14, tzinfo=UTC),
            end=datetime(2026, 1, 15, tzinfo=UTC),
        ),
    )

    # Act
    registry.register(state)

    # Assert
    result = registry.get_latest(**fake_domain).state
    actual = (result.start, result.end)
    expected = (datetime(2026, 1, 14, tzinfo=UTC), datetime(2026, 1, 15, tzinfo=UTC))
    assert actual == expected


def test_register_should_persist_int_watermark(registry: IcebergBatchRegistry, fake_domain: dict):
    # Arrange
    state = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 15, tzinfo=UTC),
        state=BatchState(watermark=42),
    )

    # Act
    registry.register(state)

    # Assert
    result = registry.get_latest(**fake_domain).state.watermark
    actual = (result, type(result))
    expected = (42, int)
    assert actual == expected


def test_register_should_persist_date_watermark(registry: IcebergBatchRegistry, fake_domain: dict):
    # Arrange
    state = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 15, tzinfo=UTC),
        state=BatchState(watermark=date(2026, 1, 15)),
    )

    # Act
    registry.register(state)

    # Assert
    result = registry.get_latest(**fake_domain).state.watermark
    actual = (result, type(result))
    expected = (date(2026, 1, 15), date)
    assert actual == expected


def test_register_should_persist_datetime_watermark(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange
    state = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 15, tzinfo=UTC),
        state=BatchState(watermark=datetime(2026, 1, 15, 10, 30, 45, 123456, tzinfo=UTC)),
    )

    # Act
    registry.register(state)

    # Assert
    result = registry.get_latest(**fake_domain).state.watermark
    actual = (result, type(result))
    expected = (datetime(2026, 1, 15, 10, 30, 45, 123456, tzinfo=UTC), datetime)
    assert actual == expected


# ============================================================================
# lifecycle transitions
# ============================================================================
def test_begin_should_persist_batch_to_running(registry: IcebergBatchRegistry, fake_domain: dict):
    # Arrange
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))
    registry.register(state)

    # Act
    registry.begin(state)

    # Assert
    actual = registry.get_latest(**fake_domain).status
    expected = BatchStatus.RUNNING
    assert actual == expected


def test_commit_should_persist_batch_to_succeeded(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))
    registry.register(state)
    registry.begin(state)

    # Act
    registry.commit(state)

    # Assert
    actual = registry.get_latest(**fake_domain).status
    expected = BatchStatus.SUCCEEDED
    assert actual == expected


def test_fail_should_persist_batch_to_failed(registry: IcebergBatchRegistry, fake_domain: dict):
    # Arrange
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))
    registry.register(state)
    registry.begin(state)

    # Act
    registry.fail(state)

    # Assert
    actual = registry.get_latest(**fake_domain).status
    expected = BatchStatus.FAILED
    assert actual == expected


def test_cancel_should_persist_batch_to_canceled(registry: IcebergBatchRegistry, fake_domain: dict):
    # Arrange
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))
    registry.register(state)

    # Act
    registry.cancel(state)

    # Assert
    actual = registry.get_latest(**fake_domain).status
    expected = BatchStatus.CANCELED
    assert actual == expected


def test_quarantine_should_persist_batch_to_quarantined(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))
    registry.register(state)
    registry.begin(state)

    # Act
    registry.quarantine(state)

    # Assert
    actual = registry.get_latest(**fake_domain).status
    expected = BatchStatus.QUARANTINED
    assert actual == expected


def test_replay_should_persist_batch_to_pending(registry: IcebergBatchRegistry, fake_domain: dict):
    # Arrange
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))
    registry.register(state)
    registry.begin(state)
    registry.commit(state)

    # Act
    registry.replay(state)

    # Assert
    actual = registry.get_latest(**fake_domain).status
    expected = BatchStatus.PENDING
    assert actual == expected


@pytest.mark.parametrize(
    "status, transition",
    [
        (BatchStatus.PENDING, lambda registry, state: registry.begin(state)),
        (BatchStatus.RUNNING, lambda registry, state: registry.commit(state)),
        (BatchStatus.RUNNING, lambda registry, state: registry.fail(state)),
        (BatchStatus.PENDING, lambda registry, state: registry.cancel(state)),
        (BatchStatus.RUNNING, lambda registry, state: registry.quarantine(state)),
        (BatchStatus.SUCCEEDED, lambda registry, state: registry.replay(state)),
    ],
)
def test_lifecycle_transition_should_raise_not_found_when_batch_is_not_registered(
    registry: IcebergBatchRegistry, fake_domain: dict, status: BatchStatus, transition
):
    # Arrange
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC), status=status)

    # Act / Assert
    with pytest.raises(BatchNotFoundError):
        transition(registry, state)


# ============================================================================
# get_latest
# ============================================================================
def test_get_latest_should_return_none_when_no_batch_matches(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange / Act
    actual = registry.get_latest(**fake_domain)

    # Assert
    expected = None
    assert actual == expected


def test_get_latest_should_return_batch_with_highest_created_at(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange
    registry.register(Batch(**fake_domain, nominal_time=datetime(2026, 1, 10, tzinfo=UTC)))
    registry.register(Batch(**fake_domain, nominal_time=datetime(2026, 1, 20, tzinfo=UTC)))
    registry.register(Batch(**fake_domain, nominal_time=datetime(2026, 1, 13, tzinfo=UTC)))

    # Act
    actual = registry.get_latest(**fake_domain).nominal_time

    # Assert
    expected = datetime(2026, 1, 13, tzinfo=UTC)
    assert actual == expected


# ============================================================================
# get_backlog
# ============================================================================
@pytest.mark.parametrize(
    "status",
    [BatchStatus.PENDING, BatchStatus.FAILED, BatchStatus.RUNNING],
)
def test_get_backlog_should_return_ongoing_states(
    registry: IcebergBatchRegistry, fake_domain: dict, status: BatchStatus
):
    # Arrange
    state = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 15, tzinfo=UTC),
        status=status,
        state=BatchState(end=datetime(2026, 1, 15, tzinfo=UTC)),
    )
    registry.register(state)

    # Act
    actual = registry.get_backlog(**fake_domain)

    # Assert
    expected = [state]
    assert actual == expected


def test_get_backlog_should_return_all_ongoing_states(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange
    pending = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 15, tzinfo=UTC),
        status=BatchStatus.PENDING,
        state=BatchState(end=datetime(2026, 1, 15, tzinfo=UTC)),
    )
    failed = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 16, tzinfo=UTC),
        status=BatchStatus.FAILED,
        state=BatchState(end=datetime(2026, 1, 16, tzinfo=UTC)),
    )
    running = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 17, tzinfo=UTC),
        status=BatchStatus.RUNNING,
        state=BatchState(end=datetime(2026, 1, 17, tzinfo=UTC)),
    )
    registry.register(pending)
    registry.register(failed)
    registry.register(running)

    # Act
    result = registry.get_backlog(**fake_domain)

    # Assert
    actual = sorted(result, key=lambda state: state.nominal_time)
    expected = [pending, failed, running]
    assert actual == expected


def test_get_backlog_should_return_nothing_when_nothing_to_process(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange / Act
    actual = registry.get_backlog(**fake_domain)

    # Assert
    expected = []
    assert actual == expected


@pytest.mark.parametrize(
    "status",
    [BatchStatus.SUCCEEDED, BatchStatus.CANCELED, BatchStatus.QUARANTINED],
)
def test_get_backlog_should_return_nothing_when_status_is_terminal(
    registry: IcebergBatchRegistry, fake_domain: dict, status: BatchStatus
):
    # Arrange
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC), status=status)
    registry.register(state)

    # Act
    actual = registry.get_backlog(**fake_domain)

    # Assert
    expected = []
    assert actual == expected


# ============================================================================
# get_history
# ============================================================================
def test_get_history_should_return_empty_when_no_batch_exists(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange / Act
    actual = registry.get_history(**fake_domain)

    # Assert
    expected = []
    assert actual == expected


def test_get_history_should_return_registered_batch(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange
    state = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 15, tzinfo=UTC),
        created_at=datetime(2026, 6, 1, tzinfo=UTC),
        state=BatchState(end=datetime(2026, 1, 15, tzinfo=UTC)),
    )
    registry.register(state)

    # Act
    actual = registry.get_history(since=datetime(2026, 1, 1, tzinfo=UTC), **fake_domain)

    # Assert
    expected = [state]
    assert actual == expected


def test_get_history_should_return_batches_ordered_by_created_at_descending(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange
    oldest = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 10, tzinfo=UTC),
        created_at=datetime(2026, 6, 1, tzinfo=UTC),
        state=BatchState(end=datetime(2026, 1, 10, tzinfo=UTC)),
    )
    middle = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 11, tzinfo=UTC),
        created_at=datetime(2026, 6, 2, tzinfo=UTC),
        state=BatchState(end=datetime(2026, 1, 11, tzinfo=UTC)),
    )
    newest = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 12, tzinfo=UTC),
        created_at=datetime(2026, 6, 3, tzinfo=UTC),
        state=BatchState(end=datetime(2026, 1, 12, tzinfo=UTC)),
    )
    registry.register(oldest)
    registry.register(middle)
    registry.register(newest)

    # Act
    actual = registry.get_history(since=datetime(2026, 1, 1, tzinfo=UTC), **fake_domain)

    # Assert
    expected = [newest, middle, oldest]
    assert actual == expected


def test_get_history_should_truncate_to_limit(registry: IcebergBatchRegistry, fake_domain: dict):
    # Arrange
    oldest = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 10, tzinfo=UTC),
        created_at=datetime(2026, 6, 1, tzinfo=UTC),
        state=BatchState(end=datetime(2026, 1, 10, tzinfo=UTC)),
    )
    middle = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 11, tzinfo=UTC),
        created_at=datetime(2026, 6, 2, tzinfo=UTC),
        state=BatchState(end=datetime(2026, 1, 11, tzinfo=UTC)),
    )
    newest = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 12, tzinfo=UTC),
        created_at=datetime(2026, 6, 3, tzinfo=UTC),
        state=BatchState(end=datetime(2026, 1, 12, tzinfo=UTC)),
    )
    registry.register(oldest)
    registry.register(middle)
    registry.register(newest)

    # Act
    actual = registry.get_history(limit=2, since=datetime(2026, 1, 1, tzinfo=UTC), **fake_domain)

    # Assert
    expected = [newest, middle]
    assert actual == expected


def test_get_history_should_exclude_batches_older_than_since(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange
    older = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 10, tzinfo=UTC),
        created_at=datetime(2026, 5, 1, tzinfo=UTC),
        state=BatchState(end=datetime(2026, 1, 10, tzinfo=UTC)),
    )
    newer = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 11, tzinfo=UTC),
        created_at=datetime(2026, 6, 1, tzinfo=UTC),
        state=BatchState(end=datetime(2026, 1, 11, tzinfo=UTC)),
    )
    registry.register(older)
    registry.register(newer)

    # Act
    actual = registry.get_history(since=datetime(2026, 5, 15, tzinfo=UTC), **fake_domain)

    # Assert
    expected = [newer]
    assert actual == expected


def test_get_history_should_scope_to_resource(registry: IcebergBatchRegistry, fake_domain: dict):
    # Arrange
    other_domain = {**fake_domain, "model": "payments"}
    target = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 10, tzinfo=UTC),
        created_at=datetime(2026, 6, 1, tzinfo=UTC),
        state=BatchState(end=datetime(2026, 1, 10, tzinfo=UTC)),
    )
    other = Batch(
        **other_domain,
        nominal_time=datetime(2026, 1, 11, tzinfo=UTC),
        created_at=datetime(2026, 6, 2, tzinfo=UTC),
        state=BatchState(end=datetime(2026, 1, 11, tzinfo=UTC)),
    )
    registry.register(target)
    registry.register(other)

    # Act
    actual = registry.get_history(since=datetime(2026, 1, 1, tzinfo=UTC), **fake_domain)

    # Assert
    expected = [target]
    assert actual == expected
