from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from pyiceberg.catalog import load_catalog
from pyiceberg.table import Table
from pyiceberg.table.sorting import NullOrder, SortDirection

from tiozin import Batch, BatchStatus
from tiozin.exceptions import BatchAlreadyExistsError, BatchNotFoundError
from tiozin.family.tio_kernel import IcebergBatchRegistry


@pytest.fixture()
def registry(tmp_path: Path):
    registry = IcebergBatchRegistry(location=str(tmp_path))
    registry.setup()
    yield registry
    registry.teardown()


def load_batch_table(location: str) -> Table:
    catalog = load_catalog(
        "tiozin",
        type="sql",
        uri=f"sqlite:///{location}/catalog.db",
        warehouse=f"file://{location}",
    )
    return catalog.load_table(("default", "tiozin_batches"))


# ============================================================================
# setup
# ============================================================================
def test_setup_should_set_id_as_identifier_field(tmp_path: Path):
    # Arrange
    registry = IcebergBatchRegistry(location=str(tmp_path))

    # Act
    registry.setup()

    # Assert
    table = load_batch_table(str(tmp_path))
    actual = table.schema().identifier_field_names()
    expected = {"id"}
    assert actual == expected


def test_setup_should_partition_by_resource_fields(tmp_path: Path):
    # Arrange
    registry = IcebergBatchRegistry(location=str(tmp_path))

    # Act
    registry.setup()

    # Assert
    table = load_batch_table(str(tmp_path))
    actual = [field.name for field in table.spec().fields]
    expected = ["org", "region", "domain", "subdomain", "layer", "product", "model"]
    assert actual == expected


def test_setup_should_sort_by_created_at_ascending(tmp_path: Path):
    # Arrange
    registry = IcebergBatchRegistry(location=str(tmp_path))

    # Act
    registry.setup()

    # Assert
    table = load_batch_table(str(tmp_path))
    actual = [
        (table.schema().find_column_name(field.source_id), field.direction, field.null_order)
        for field in table.sort_order().fields
    ]
    expected = [("created_at", SortDirection.ASC, NullOrder.NULLS_LAST)]
    assert actual == expected


def test_setup_should_create_table_with_format_version_2(tmp_path: Path):
    # Arrange
    registry = IcebergBatchRegistry(location=str(tmp_path))

    # Act
    registry.setup()

    # Assert
    table = load_batch_table(str(tmp_path))
    actual = table.metadata.format_version
    expected = 2
    assert actual == expected


def test_setup_should_configure_table_properties(tmp_path: Path):
    # Arrange
    registry = IcebergBatchRegistry(location=str(tmp_path), retention_days=10)

    # Act
    registry.setup()

    # Assert
    table = load_batch_table(str(tmp_path))
    actual = dict(table.properties)
    expected = {
        "history.expire.min-snapshots-to-keep": "7",
        "history.expire.max-snapshot-age-ms": "864000000",
    }
    assert actual == expected


def test_setup_should_not_duplicate_partition_fields_when_called_twice(tmp_path: Path):
    # Arrange
    registry = IcebergBatchRegistry(location=str(tmp_path))

    # Act
    registry.setup()
    registry.setup()

    # Assert
    table = load_batch_table(str(tmp_path))
    actual = [field.name for field in table.spec().fields]
    expected = ["org", "region", "domain", "subdomain", "layer", "product", "model"]
    assert actual == expected


# ============================================================================
# register
# ============================================================================
def test_register_should_persist_all_fields(registry: IcebergBatchRegistry, fake_domain: dict):
    # Arrange
    state = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 15, tzinfo=UTC),
    )

    # Act
    registry.register(state)

    # Assert
    actual = registry.get_frontier(**fake_domain)
    expected = state
    assert actual == expected


def test_register_should_persist_nominal_window(registry: IcebergBatchRegistry, fake_domain: dict):
    # Arrange
    state = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 15, tzinfo=UTC),
        nominal_start_time=datetime(2026, 1, 1, tzinfo=UTC),
        nominal_end_time=datetime(2026, 1, 14, tzinfo=UTC),
    )

    # Act
    registry.register(state)

    # Assert
    reloaded = registry.get_frontier(**fake_domain)
    actual = (
        reloaded.nominal_start_time,
        reloaded.nominal_end_time,
    )
    expected = (
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 14, tzinfo=UTC),
    )
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
    actual = registry.get_frontier(**fake_domain).attributes
    expected = {"extra1": "value1", "existing1": "value2"}
    assert actual == expected


def test_register_should_persist_bookmarks(registry: IcebergBatchRegistry, fake_domain: dict):
    # Arrange
    state = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 15, tzinfo=UTC),
        bookmarks={
            "cursor": 42,
            "watermark_at": datetime(2026, 1, 15, 10, 30, tzinfo=UTC),
            "watermark_on": date(2026, 1, 15),
        },
    )

    # Act
    registry.register(state)

    # Assert
    actual = registry.get_frontier(**fake_domain).bookmarks
    expected = {
        "cursor": 42,
        "watermark_at": datetime(2026, 1, 15, 10, 30, tzinfo=UTC),
        "watermark_on": date(2026, 1, 15),
    }
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
    actual = registry.get_frontier(**fake_domain).attributes
    expected = {"extra1": None}
    assert actual == expected


def test_register_should_persist_datetime_and_date_attributes_with_their_types(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange
    state = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 15, tzinfo=UTC),
        attributes={
            "seen_at": datetime(2026, 1, 15, 10, 30, tzinfo=UTC),
            "seen_on": date(2026, 1, 15),
        },
    )

    # Act
    registry.register(state)

    # Assert
    actual = registry.get_frontier(**fake_domain).attributes
    expected = {
        "seen_at": datetime(2026, 1, 15, 10, 30, tzinfo=UTC),
        "seen_on": date(2026, 1, 15),
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
# register_transition
# ============================================================================
@pytest.mark.parametrize(
    "status",
    [
        BatchStatus.RUNNING,
        BatchStatus.SUCCEEDED,
        BatchStatus.FAILED,
        BatchStatus.CANCELED,
        BatchStatus.QUARANTINED,
    ],
)
def test_register_transition_should_persist_new_status(
    registry: IcebergBatchRegistry, fake_domain: dict, status: BatchStatus
):
    # Arrange
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))
    registry.register(state)
    state.status = status

    # Act
    registry.register_transition(state)

    # Assert
    actual = registry.get(state.id, **fake_domain).status
    expected = status
    assert actual == expected


def test_register_transition_should_persist_updated_attributes(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange
    state = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 15, tzinfo=UTC),
        attributes={"existing1": "value1"},
    )
    registry.register(state)
    state.attributes = {"existing1": "value1", "extra1": "value2"}

    # Act
    registry.register_transition(state)

    # Assert
    actual = registry.get_frontier(**fake_domain).attributes
    expected = {"existing1": "value1", "extra1": "value2"}
    assert actual == expected


def test_register_transition_should_raise_not_found_when_batch_is_not_registered(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange
    state = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 15, tzinfo=UTC),
        status=BatchStatus.RUNNING,
    )

    # Act / Assert
    with pytest.raises(BatchNotFoundError):
        registry.register_transition(state)


# ============================================================================
# get_frontier
# ============================================================================
def test_get_frontier_should_return_none_when_no_batch_matches(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange / Act
    actual = registry.get_frontier(**fake_domain)

    # Assert
    expected = None
    assert actual == expected


def test_get_frontier_should_return_batch_with_highest_created_at(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange
    registry.register(Batch(**fake_domain, nominal_time=datetime(2026, 1, 10, tzinfo=UTC)))
    registry.register(Batch(**fake_domain, nominal_time=datetime(2026, 1, 20, tzinfo=UTC)))
    registry.register(Batch(**fake_domain, nominal_time=datetime(2026, 1, 13, tzinfo=UTC)))

    # Act
    actual = registry.get_frontier(**fake_domain).nominal_time

    # Assert
    expected = datetime(2026, 1, 13, tzinfo=UTC)
    assert actual == expected


def test_get_frontier_should_return_latest_active_batch_when_newest_is_cancelled(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange
    active = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 10, tzinfo=UTC),
        created_at=datetime(2026, 6, 1, tzinfo=UTC),
    )
    cancelled = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 20, tzinfo=UTC),
        created_at=datetime(2026, 6, 2, tzinfo=UTC),
        status=BatchStatus.CANCELED,
    )
    registry.register(active)
    registry.register(cancelled)

    # Act
    actual = registry.get_frontier(**fake_domain)

    # Assert
    expected = active
    assert actual == expected


def test_get_frontier_should_return_none_when_all_batches_are_cancelled(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange
    older = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 10, tzinfo=UTC),
        status=BatchStatus.CANCELED,
    )
    newer = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 20, tzinfo=UTC),
        status=BatchStatus.CANCELED,
    )
    registry.register(older)
    registry.register(newer)

    # Act
    actual = registry.get_frontier(**fake_domain)

    # Assert
    expected = None
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
    )
    failed = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 16, tzinfo=UTC),
        status=BatchStatus.FAILED,
    )
    running = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 17, tzinfo=UTC),
        status=BatchStatus.RUNNING,
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
# get_board
# ============================================================================
def test_get_board_should_return_empty_when_no_batch_exists(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange / Act
    actual = registry.get_board(**fake_domain)

    # Assert
    expected = []
    assert actual == expected


def test_get_board_should_return_registered_batch(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange
    state = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 15, tzinfo=UTC),
        created_at=datetime(2026, 6, 1, tzinfo=UTC),
    )
    registry.register(state)

    # Act
    actual = registry.get_board(since=datetime(2026, 1, 1, tzinfo=UTC), **fake_domain)

    # Assert
    expected = [state]
    assert actual == expected


def test_get_board_should_return_batches_ordered_by_created_at_descending(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange
    oldest = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 10, tzinfo=UTC),
        created_at=datetime(2026, 6, 1, tzinfo=UTC),
    )
    middle = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 11, tzinfo=UTC),
        created_at=datetime(2026, 6, 2, tzinfo=UTC),
    )
    newest = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 12, tzinfo=UTC),
        created_at=datetime(2026, 6, 3, tzinfo=UTC),
    )
    registry.register(oldest)
    registry.register(middle)
    registry.register(newest)

    # Act
    actual = registry.get_board(since=datetime(2026, 1, 1, tzinfo=UTC), **fake_domain)

    # Assert
    expected = [newest, middle, oldest]
    assert actual == expected


def test_get_board_should_truncate_to_limit(registry: IcebergBatchRegistry, fake_domain: dict):
    # Arrange
    oldest = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 10, tzinfo=UTC),
        created_at=datetime(2026, 6, 1, tzinfo=UTC),
    )
    middle = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 11, tzinfo=UTC),
        created_at=datetime(2026, 6, 2, tzinfo=UTC),
    )
    newest = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 12, tzinfo=UTC),
        created_at=datetime(2026, 6, 3, tzinfo=UTC),
    )
    registry.register(oldest)
    registry.register(middle)
    registry.register(newest)

    # Act
    actual = registry.get_board(limit=2, since=datetime(2026, 1, 1, tzinfo=UTC), **fake_domain)

    # Assert
    expected = [newest, middle]
    assert actual == expected


def test_get_board_should_exclude_batches_older_than_since(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange
    older = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 10, tzinfo=UTC),
        created_at=datetime(2026, 5, 1, tzinfo=UTC),
    )
    newer = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 11, tzinfo=UTC),
        created_at=datetime(2026, 6, 1, tzinfo=UTC),
    )
    registry.register(older)
    registry.register(newer)

    # Act
    actual = registry.get_board(since=datetime(2026, 5, 15, tzinfo=UTC), **fake_domain)

    # Assert
    expected = [newer]
    assert actual == expected


def test_get_board_should_scope_to_resource(registry: IcebergBatchRegistry, fake_domain: dict):
    # Arrange
    other_domain = {**fake_domain, "model": "payments"}
    target = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 10, tzinfo=UTC),
        created_at=datetime(2026, 6, 1, tzinfo=UTC),
    )
    other = Batch(
        **other_domain,
        nominal_time=datetime(2026, 1, 11, tzinfo=UTC),
        created_at=datetime(2026, 6, 2, tzinfo=UTC),
    )
    registry.register(target)
    registry.register(other)

    # Act
    actual = registry.get_board(since=datetime(2026, 1, 1, tzinfo=UTC), **fake_domain)

    # Assert
    expected = [target]
    assert actual == expected
