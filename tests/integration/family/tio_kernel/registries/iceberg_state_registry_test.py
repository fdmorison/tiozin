from pathlib import Path

import pytest
from pyiceberg.catalog import load_catalog

from tiozin.api import State
from tiozin.api.metadata.state.status import StateStatus
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


def test_register_should_replace_state_when_same_natural_key_registered_twice(
    registry: IcebergStateRegistry, fake_domain: dict
):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    registry.register(state)
    registry.register(state)

    # Assert
    rows = _scan_table(registry.location)
    actual = [row["id"] for row in rows]
    expected = [state.id]
    assert actual == expected


# ============================================================================
# lifecycle transitions
# ============================================================================
def test_begin_should_persist_state_to_running(registry: IcebergStateRegistry, fake_domain: dict):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    registry.begin(state)

    # Assert
    row = _scan_table(registry.location)[0]
    actual = row["status"]
    expected = StateStatus.RUNNING
    assert actual == expected


def test_commit_should_persist_state_to_succeeded(
    registry: IcebergStateRegistry, fake_domain: dict
):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15")
    registry.begin(state)

    # Act
    registry.commit(state)

    # Assert
    row = _scan_table(registry.location)[0]
    actual = row["status"]
    expected = StateStatus.SUCCEEDED
    assert actual == expected


def test_fail_should_persist_state_to_failed(registry: IcebergStateRegistry, fake_domain: dict):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15")
    registry.begin(state)

    # Act
    registry.fail(state)

    # Assert
    row = _scan_table(registry.location)[0]
    actual = row["status"]
    expected = StateStatus.FAILED
    assert actual == expected


def test_cancel_should_persist_state_to_canceled(registry: IcebergStateRegistry, fake_domain: dict):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    registry.cancel(state)

    # Assert
    row = _scan_table(registry.location)[0]
    actual = row["status"]
    expected = StateStatus.CANCELED
    assert actual == expected


def test_quarantine_should_persist_state_to_quarantined(
    registry: IcebergStateRegistry, fake_domain: dict
):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15")
    registry.begin(state)

    # Act
    registry.quarantine(state)

    # Assert
    row = _scan_table(registry.location)[0]
    actual = row["status"]
    expected = StateStatus.QUARANTINED
    assert actual == expected


def test_replay_should_persist_state_to_pending(registry: IcebergStateRegistry, fake_domain: dict):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15")
    registry.begin(state)
    registry.commit(state)

    # Act
    registry.replay(state)

    # Assert
    row = _scan_table(registry.location)[0]
    actual = row["status"]
    expected = StateStatus.PENDING
    assert actual == expected


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
    [StateStatus.PENDING, StateStatus.FAILED, StateStatus.RUNNING],
)
def test_get_backlog_should_return_ongoing_states(
    registry: IcebergStateRegistry, fake_domain: dict, status: StateStatus
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
    pending = State(**fake_domain, batch_key="2026-01-15", status=StateStatus.PENDING)
    failed = State(**fake_domain, batch_key="2026-01-16", status=StateStatus.FAILED)
    running = State(**fake_domain, batch_key="2026-01-17", status=StateStatus.RUNNING)
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
    [StateStatus.SUCCEEDED, StateStatus.CANCELED, StateStatus.QUARANTINED],
)
def test_get_backlog_should_return_nothing_when_status_is_terminal(
    registry: IcebergStateRegistry, fake_domain: dict, status: StateStatus
):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15", status=status)
    registry.register(state)

    # Act
    actual = registry.get_backlog(**fake_domain)

    # Assert
    expected = []
    assert actual == expected
