from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from pyiceberg.catalog import load_catalog
from pyiceberg.table import Table
from pyiceberg.table.sorting import NullOrder, SortDirection

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
def test_register_should_persist_default_start_as_epoch_and_watermarks_as_empty(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    registry.register(state)

    # Assert
    result = registry.get_latest(**fake_domain).state
    actual = (result.start, result.watermarks)
    expected = (
        datetime(1970, 1, 1, tzinfo=UTC),
        {},
    )
    assert actual == expected


def test_register_should_persist_default_end_as_registration_time_truncated_to_minute(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange
    before = datetime.now(UTC).replace(second=0, microsecond=0)
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    registry.register(state)

    # Assert
    after = datetime.now(UTC).replace(second=0, microsecond=0)
    result = registry.get_latest(**fake_domain).state
    assert before <= result.end <= after


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
        state=BatchState(watermarks={"orders": 42}),
    )

    # Act
    registry.register(state)

    # Assert
    result = registry.get_latest(**fake_domain).state.watermarks["orders"]
    actual = (result, type(result))
    expected = (42, int)
    assert actual == expected


def test_register_should_persist_date_watermark(registry: IcebergBatchRegistry, fake_domain: dict):
    # Arrange
    state = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 15, tzinfo=UTC),
        state=BatchState(watermarks={"orders": date(2026, 1, 15)}),
    )

    # Act
    registry.register(state)

    # Assert
    result = registry.get_latest(**fake_domain).state.watermarks["orders"]
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
        state=BatchState(
            watermarks={"orders": datetime(2026, 1, 15, 10, 30, 45, 123456, tzinfo=UTC)}
        ),
    )

    # Act
    registry.register(state)

    # Assert
    result = registry.get_latest(**fake_domain).state.watermarks["orders"]
    actual = (result, type(result))
    expected = (datetime(2026, 1, 15, 10, 30, 45, 123456, tzinfo=UTC), datetime)
    assert actual == expected


def test_register_should_persist_none_watermark(registry: IcebergBatchRegistry, fake_domain: dict):
    # Arrange
    state = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 15, tzinfo=UTC),
        state=BatchState(watermarks={"orders": None}),
    )

    # Act
    registry.register(state)

    # Assert
    actual = registry.get_latest(**fake_domain).state.watermarks
    expected = {"orders": None}
    assert actual == expected


def test_register_should_persist_one_watermark_per_source(
    registry: IcebergBatchRegistry, fake_domain: dict
):
    # Arrange
    state = Batch(
        **fake_domain,
        nominal_time=datetime(2026, 1, 15, tzinfo=UTC),
        state=BatchState(
            watermarks={
                "orders": 42,
                "customers": date(2026, 1, 15),
                "events": datetime(2026, 1, 15, 10, 30, 45, 123456, tzinfo=UTC),
            }
        ),
    )

    # Act
    registry.register(state)

    # Assert
    actual = registry.get_latest(**fake_domain).state.watermarks
    expected = {
        "orders": 42,
        "customers": date(2026, 1, 15),
        "events": datetime(2026, 1, 15, 10, 30, 45, 123456, tzinfo=UTC),
    }
    assert actual == expected


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
    actual = registry.get_latest(**fake_domain).status
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
    actual = registry.get_latest(**fake_domain).attributes
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
        state=BatchState(end=datetime(2026, 1, 15, tzinfo=UTC)),
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
    actual = registry.get_board(since=datetime(2026, 1, 1, tzinfo=UTC), **fake_domain)

    # Assert
    expected = [target]
    assert actual == expected
