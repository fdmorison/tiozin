from pathlib import Path

import pytest
from pyiceberg.catalog import load_catalog

from tiozin.api import BatchStatus, State
from tiozin.api.metadata.state.exceptions import StateAlreadyExistsError, StateNotFoundError
from tiozin.family.tio_kernel import IcebergStateRegistry


@pytest.fixture()
def registry(tmp_path: Path):
    registry = IcebergStateRegistry(location=str(tmp_path))
    registry.setup()
    yield registry
    registry.teardown()


def _scan_table(location: str) -> list[dict]:
    catalog = load_catalog(
        "default",
        type="sql",
        uri=f"sqlite:///{location}/catalog.db",
        warehouse=f"file://{location}",
    )
    return catalog.load_table(("tiozin", "state")).scan().to_arrow().to_pylist()


# ============================================================================
# register
# ============================================================================
def test_register_should_persist_all_fields_to_iceberg_table(
    registry: IcebergStateRegistry, fake_domain: dict
):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15")

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
        "batch_key": state.batch_key,
        "status": state.status,
        "attributes": state.attributes,
        "created_at": state.created_at,
        "updated_at": state.updated_at,
    }
    assert actual == expected


def test_register_should_raise_when_natural_key_already_exists(
    registry: IcebergStateRegistry, fake_domain: dict
):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15")
    registry.register(state)

    # Act / Assert
    with pytest.raises(StateAlreadyExistsError):
        registry.register(state)


# ============================================================================
# lifecycle transitions
# ============================================================================
def test_begin_should_persist_state_to_running(registry: IcebergStateRegistry, fake_domain: dict):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15")
    registry.register(state)

    # Act
    registry.begin(state)

    # Assert
    row = _scan_table(registry.location)[0]
    actual = row["status"]
    expected = BatchStatus.RUNNING
    assert actual == expected


def test_commit_should_persist_state_to_succeeded(
    registry: IcebergStateRegistry, fake_domain: dict
):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15")
    registry.register(state)
    registry.begin(state)

    # Act
    registry.commit(state)

    # Assert
    row = _scan_table(registry.location)[0]
    actual = row["status"]
    expected = BatchStatus.SUCCEEDED
    assert actual == expected


def test_fail_should_persist_state_to_failed(registry: IcebergStateRegistry, fake_domain: dict):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15")
    registry.register(state)
    registry.begin(state)

    # Act
    registry.fail(state)

    # Assert
    row = _scan_table(registry.location)[0]
    actual = row["status"]
    expected = BatchStatus.FAILED
    assert actual == expected


def test_cancel_should_persist_state_to_canceled(registry: IcebergStateRegistry, fake_domain: dict):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15")
    registry.register(state)

    # Act
    registry.cancel(state)

    # Assert
    row = _scan_table(registry.location)[0]
    actual = row["status"]
    expected = BatchStatus.CANCELED
    assert actual == expected


def test_quarantine_should_persist_state_to_quarantined(
    registry: IcebergStateRegistry, fake_domain: dict
):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15")
    registry.register(state)
    registry.begin(state)

    # Act
    registry.quarantine(state)

    # Assert
    row = _scan_table(registry.location)[0]
    actual = row["status"]
    expected = BatchStatus.QUARANTINED
    assert actual == expected


def test_replay_should_persist_state_to_pending(registry: IcebergStateRegistry, fake_domain: dict):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15")
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
def test_lifecycle_transition_should_raise_not_found_when_state_is_not_registered(
    registry: IcebergStateRegistry, fake_domain: dict, status: BatchStatus, transition
):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15", status=status)

    # Act / Assert
    with pytest.raises(StateNotFoundError):
        transition(registry, state)


# ============================================================================
# get_watermark
# ============================================================================
def test_get_watermark_should_return_none_when_no_state_matches(
    registry: IcebergStateRegistry, fake_domain: dict
):
    # Arrange / Act
    actual = registry.get_watermark(**fake_domain)

    # Assert
    expected = None
    assert actual == expected


def test_get_watermark_should_return_state_with_highest_batch_key(
    registry: IcebergStateRegistry, fake_domain: dict
):
    # Arrange
    registry.register(State(**fake_domain, batch_key="2026-01-10"))
    registry.register(State(**fake_domain, batch_key="2026-01-20"))
    registry.register(State(**fake_domain, batch_key="2026-01-13"))

    # Act
    actual = registry.get_watermark(**fake_domain).batch_key

    # Assert
    expected = "2026-01-20"
    assert actual == expected


# ============================================================================
# get_backlog
# ============================================================================
@pytest.mark.parametrize(
    "status",
    [BatchStatus.PENDING, BatchStatus.FAILED, BatchStatus.RUNNING],
)
def test_get_backlog_should_return_ongoing_states(
    registry: IcebergStateRegistry, fake_domain: dict, status: BatchStatus
):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15", status=status)
    registry.register(state)

    # Act
    actual = registry.get_backlog(**fake_domain)

    # Assert
    expected = [state]
    assert actual == expected


def test_get_backlog_should_return_all_ongoing_states(
    registry: IcebergStateRegistry, fake_domain: dict
):
    # Arrange
    pending = State(**fake_domain, batch_key="2026-01-15", status=BatchStatus.PENDING)
    failed = State(**fake_domain, batch_key="2026-01-16", status=BatchStatus.FAILED)
    running = State(**fake_domain, batch_key="2026-01-17", status=BatchStatus.RUNNING)
    registry.register(pending)
    registry.register(failed)
    registry.register(running)

    # Act
    result = registry.get_backlog(**fake_domain)

    # Assert
    actual = sorted(result, key=lambda state: state.batch_key)
    expected = [pending, failed, running]
    assert actual == expected


def test_get_backlog_should_return_nothing_when_nothing_to_process(
    registry: IcebergStateRegistry, fake_domain: dict
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
    registry: IcebergStateRegistry, fake_domain: dict, status: BatchStatus
):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15", status=status)
    registry.register(state)

    # Act
    actual = registry.get_backlog(**fake_domain)

    # Assert
    expected = []
    assert actual == expected
