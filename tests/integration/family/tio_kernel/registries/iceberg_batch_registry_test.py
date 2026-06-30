from datetime import UTC, datetime
from pathlib import Path

import pytest
from pyiceberg.catalog import load_catalog

from tiozin.api import Batch, BatchStatus
from tiozin.exceptions import BatchAlreadyExistsError, BatchNotFoundError
from tiozin.family.tio_kernel import IcebergBatchRegistry


@pytest.fixture()
def registry(tmp_path: Path):
    registry = IcebergBatchRegistry(location=str(tmp_path))
    registry.setup()
    yield registry
    registry.teardown()


def _scan_table(location: str) -> list[dict]:
    catalog = load_catalog(
        "tiozin",
        type="sql",
        uri=f"sqlite:///{location}/catalog.db",
        warehouse=f"file://{location}",
    )
    return catalog.load_table("tiozin.tiozin_batches").scan().to_arrow().to_pylist()


# ============================================================================
# register
# ============================================================================
def test_register_should_persist_all_fields_to_iceberg_table(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    registry.register(state)

    # Assert
    row = _scan_table(registry.location)[0]
    actual = {**row, "attributes": dict(row["attributes"])}
    expected = {
        "id": state.id,
        "org": state.org,
        "region": state.region,
        "domain": state.domain,
        "subdomain": state.subdomain,
        "layer": state.layer,
        "product": state.product,
        "model": state.model,
        "nominal_time": state.nominal_time,
        "status": state.status,
        "attributes": state.attributes,
        "created_at": state.created_at,
        "updated_at": state.updated_at,
    }
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
# lifecycle transitions
# ============================================================================
def test_begin_should_persist_batch_to_running(registry: IcebergBatchRegistry, fake_domain: dict):
    # Arrange
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))
    registry.register(state)

    # Act
    registry.begin(state)

    # Assert
    row = _scan_table(registry.location)[0]
    actual = row["status"]
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
    row = _scan_table(registry.location)[0]
    actual = row["status"]
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
    row = _scan_table(registry.location)[0]
    actual = row["status"]
    expected = BatchStatus.FAILED
    assert actual == expected


def test_cancel_should_persist_batch_to_canceled(registry: IcebergBatchRegistry, fake_domain: dict):
    # Arrange
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))
    registry.register(state)

    # Act
    registry.cancel(state)

    # Assert
    row = _scan_table(registry.location)[0]
    actual = row["status"]
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
    row = _scan_table(registry.location)[0]
    actual = row["status"]
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
    row = _scan_table(registry.location)[0]
    actual = row["status"]
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
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC), status=status)
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
        **fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC), status=BatchStatus.PENDING
    )
    failed = Batch(
        **fake_domain, nominal_time=datetime(2026, 1, 16, tzinfo=UTC), status=BatchStatus.FAILED
    )
    running = Batch(
        **fake_domain, nominal_time=datetime(2026, 1, 17, tzinfo=UTC), status=BatchStatus.RUNNING
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
