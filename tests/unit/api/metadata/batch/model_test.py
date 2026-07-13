from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from tiozin import Batch, BatchStatus
from tiozin.api.metadata.batch.state import BatchState
from tiozin.exceptions.misc import ModelError

EXPLICIT_ID = "explicit-id-1234"

# Default nominal_time for a test batch, and the value reassignment tests
# attempt to set on frozen/mutable fields.
NOMINAL_TIME = datetime(2026, 1, 15, tzinfo=UTC)
REASSIGNED_TIME = datetime(2026, 2, 1, tzinfo=UTC)

# Time constants for the acquire flow, named after their semantic role.
# Context always exposes a minute-truncated nominal_time, so these are the
# canonical (already :00) forms.
PREVIOUS_START = datetime(2026, 1, 15, tzinfo=UTC)
PREVIOUS_END = datetime(2026, 1, 15, 10, 30, tzinfo=UTC)
CURRENT_START = datetime(2026, 1, 17, tzinfo=UTC)
CURRENT_NOMINAL_TIME = datetime(2026, 1, 16, 8, 15, tzinfo=UTC)


@pytest.fixture
def registry() -> MagicMock:
    mock = MagicMock()
    with patch("tiozin.api.metadata.batch.model.Batch._registry", return_value=mock):
        yield mock


# ============================================================================
# construction / validation
# ============================================================================
def test_id_should_be_chronologically_sortable_when_not_provided(fake_domain: dict):
    # Arrange / Act
    first = Batch(**fake_domain, nominal_time=NOMINAL_TIME)
    second = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Assert
    assert second.id > first.id


def test_id_should_be_preserved_when_provided(fake_domain: dict):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, id=EXPLICIT_ID)

    # Act
    actual = batch.id

    # Assert
    expected = EXPLICIT_ID
    assert actual == expected


def test_status_should_default_to_pending(fake_domain: dict):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    actual = batch.status

    # Assert
    expected = BatchStatus.PENDING
    assert actual == expected


def test_failure_count_should_default_to_zero(fake_domain: dict):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    actual = batch.failure_count

    # Assert
    expected = 0
    assert actual == expected


def test_attributes_should_default_to_empty_dict(fake_domain: dict):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    actual = batch.attributes

    # Assert
    expected = {}
    assert actual == expected


def test_batch_should_raise_when_failure_count_is_negative(fake_domain: dict):
    # Act / Assert
    with pytest.raises(ModelError):
        Batch(
            **fake_domain,
            nominal_time=NOMINAL_TIME,
            failure_count=-1,
        )


# ============================================================================
# frozen fields
# ============================================================================
@pytest.mark.parametrize(
    "field, value",
    [
        ("id", "other-id"),
        ("org", "globex"),
        ("region", "emea"),
        ("domain", "marketing"),
        ("subdomain", "campaigns"),
        ("layer", "silver"),
        ("product", "leads"),
        ("model", "contacts"),
        ("nominal_time", REASSIGNED_TIME),
        ("created_at", REASSIGNED_TIME),
    ],
)
def test_batch_should_raise_when_frozen_field_is_reassigned(field, value, fake_domain: dict):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act / Assert
    with pytest.raises(ValidationError):
        setattr(batch, field, value)


@pytest.mark.parametrize(
    "field, value",
    [
        ("status", BatchStatus.SUCCEEDED),
        ("failure_count", 3),
        ("attributes", {"extra1": "value1"}),
        ("updated_at", REASSIGNED_TIME),
    ],
)
def test_batch_should_reassign_when_mutable_field_is_set(field, value, fake_domain: dict):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    setattr(batch, field, value)

    # Assert
    actual = getattr(batch, field)
    expected = value
    assert actual == expected


# ============================================================================
# computed properties - keys
# ============================================================================
def test_qualified_resource_should_join_resource_fields_with_dots():
    # Arrange
    batch = Batch(
        org="acme",
        region="us-east",
        domain="sales",
        subdomain="orders",
        layer="bronze",
        product="catalog",
        model="products",
        nominal_time=NOMINAL_TIME,
    )

    # Act
    actual = batch.qualified_resource

    # Assert
    expected = "acme.us-east.sales.orders.bronze.catalog.products"
    assert actual == expected


def test_qualified_natural_key_should_append_nominal_time_to_qualified_resource():
    # Arrange
    batch = Batch(
        org="acme",
        region="us-east",
        domain="sales",
        subdomain="orders",
        layer="bronze",
        product="catalog",
        model="products",
        nominal_time=NOMINAL_TIME,
    )

    # Act
    actual = batch.qualified_natural_key

    # Assert
    expected = "acme.us-east.sales.orders.bronze.catalog.products.2026-01-15T00:00:00Z"
    assert actual == expected


# ============================================================================
# lifecycle - register (delegation)
# ============================================================================
def test_register_should_delegate_to_registry(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    batch.register()

    # Assert
    registry.register.assert_called_once_with(batch)


def test_register_should_return_registry_result(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    result = batch.register()

    # Assert
    actual = result
    expected = registry.register.return_value
    assert actual is expected


def test_register_should_return_self_when_registry_returns_none(registry: MagicMock, fake_domain):
    # Arrange
    registry.register.return_value = None
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    result = batch.register()

    # Assert
    assert result is batch


# ============================================================================
# lifecycle - begin (delegation)
# ============================================================================
def test_begin_should_delegate_to_registry(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    batch.begin(extra1="value1")

    # Assert
    registry.begin.assert_called_once_with(batch, extra1="value1")


def test_begin_should_return_registry_result(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    result = batch.begin()

    # Assert
    actual = result
    expected = registry.begin.return_value
    assert actual is expected


def test_begin_should_return_self_when_registry_returns_none(registry: MagicMock, fake_domain):
    # Arrange
    registry.begin.return_value = None
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    result = batch.begin()

    # Assert
    assert result is batch


# ============================================================================
# lifecycle - commit (delegation)
# ============================================================================
def test_commit_should_delegate_to_registry(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    batch.commit(extra1="value1")

    # Assert
    registry.commit.assert_called_once_with(batch, extra1="value1")


def test_commit_should_return_registry_result(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    result = batch.commit()

    # Assert
    actual = result
    expected = registry.commit.return_value
    assert actual is expected


def test_commit_should_return_self_when_registry_returns_none(registry: MagicMock, fake_domain):
    # Arrange
    registry.commit.return_value = None
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    result = batch.commit()

    # Assert
    assert result is batch


# ============================================================================
# lifecycle - fail (delegation)
# ============================================================================
def test_fail_should_delegate_to_registry(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    batch.fail(extra1="value1")

    # Assert
    registry.fail.assert_called_once_with(batch, extra1="value1")


def test_fail_should_return_registry_result(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    result = batch.fail()

    # Assert
    actual = result
    expected = registry.fail.return_value
    assert actual is expected


def test_fail_should_return_self_when_registry_returns_none(registry: MagicMock, fake_domain):
    # Arrange
    registry.fail.return_value = None
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    result = batch.fail()

    # Assert
    assert result is batch


# ============================================================================
# lifecycle - cancel (delegation)
# ============================================================================
def test_cancel_should_delegate_to_registry(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    batch.cancel(extra1="value1")

    # Assert
    registry.cancel.assert_called_once_with(batch, extra1="value1")


def test_cancel_should_return_registry_result(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    result = batch.cancel()

    # Assert
    actual = result
    expected = registry.cancel.return_value
    assert actual is expected


def test_cancel_should_return_self_when_registry_returns_none(registry: MagicMock, fake_domain):
    # Arrange
    registry.cancel.return_value = None
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    result = batch.cancel()

    # Assert
    assert result is batch


# ============================================================================
# lifecycle - quarantine (delegation)
# ============================================================================
def test_quarantine_should_delegate_to_registry(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    batch.quarantine(extra1="value1")

    # Assert
    registry.quarantine.assert_called_once_with(batch, extra1="value1")


def test_quarantine_should_return_registry_result(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    result = batch.quarantine()

    # Assert
    actual = result
    expected = registry.quarantine.return_value
    assert actual is expected


def test_quarantine_should_return_self_when_registry_returns_none(registry: MagicMock, fake_domain):
    # Arrange
    registry.quarantine.return_value = None
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    result = batch.quarantine()

    # Assert
    assert result is batch


# ============================================================================
# lifecycle - replay (delegation)
# ============================================================================
def test_replay_should_delegate_to_registry(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    batch.replay(extra1="value1")

    # Assert
    registry.replay.assert_called_once_with(batch, extra1="value1")


def test_replay_should_return_registry_result(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    result = batch.replay()

    # Assert
    actual = result
    expected = registry.replay.return_value
    assert actual is expected


def test_replay_should_return_self_when_registry_returns_none(registry: MagicMock, fake_domain):
    # Arrange
    registry.replay.return_value = None
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    result = batch.replay()

    # Assert
    assert result is batch


# ============================================================================
# acquire
# ============================================================================
@patch("tiozin.api.context.Context.current")
def test_acquire_should_reuse_previous_batch_when_not_terminal(current, fake_domain):
    # Arrange
    previous = Batch(
        **fake_domain,
        nominal_time=PREVIOUS_START,
        status=BatchStatus.RUNNING,
    )
    current.return_value.configure_mock(**fake_domain)
    current.return_value.nominal_time = CURRENT_START
    current.return_value.registries.batch.get_latest.return_value = previous

    # Act
    actual = Batch.acquire()

    # Assert
    expected = previous
    assert actual is expected


@patch("tiozin.api.context.Context.current")
def test_acquire_should_register_new_batch_when_previous_is_terminal(current, fake_domain):
    # Arrange
    previous = Batch(
        **fake_domain,
        nominal_time=PREVIOUS_START,
        status=BatchStatus.SUCCEEDED,
    )
    current.return_value.configure_mock(**fake_domain)
    current.return_value.nominal_time = CURRENT_START
    current.return_value.registries.batch.get_latest.return_value = previous
    current.return_value.registries.batch.register.side_effect = lambda batch: batch

    # Act
    actual = Batch.acquire().nominal_time

    # Assert
    expected = CURRENT_START
    assert actual == expected


@patch("tiozin.api.context.Context.current")
def test_acquire_should_carry_watermarks_forward_from_previous_state(current, fake_domain):
    # Arrange
    previous = Batch(
        **fake_domain,
        nominal_time=PREVIOUS_START,
        status=BatchStatus.SUCCEEDED,
        state=BatchState(watermarks={"orders": 42}),
    )
    current.return_value.configure_mock(**fake_domain)
    current.return_value.nominal_time = CURRENT_START
    current.return_value.registries.batch.get_latest.return_value = previous
    current.return_value.registries.batch.register.side_effect = lambda batch: batch

    # Act
    actual = Batch.acquire().state.watermarks

    # Assert
    expected = {"orders": 42}
    assert actual == expected


@patch("tiozin.api.context.Context.current")
def test_acquire_should_derive_window_from_previous_end(current, fake_domain):
    # Arrange
    previous = Batch(
        **fake_domain,
        nominal_time=PREVIOUS_START,
        status=BatchStatus.SUCCEEDED,
        state=BatchState(
            start=datetime(2026, 1, 14, tzinfo=UTC),
            end=PREVIOUS_END,
        ),
    )
    current.return_value.configure_mock(**fake_domain)
    current.return_value.nominal_time = CURRENT_NOMINAL_TIME
    current.return_value.registries.batch.get_latest.return_value = previous
    current.return_value.registries.batch.register.side_effect = lambda batch: batch

    # Act
    result = Batch.acquire().state

    # Assert
    actual = (result.start, result.end)
    expected = (
        PREVIOUS_END,
        CURRENT_NOMINAL_TIME,
    )
    assert actual == expected


@patch("tiozin.api.context.Context.current")
def test_acquire_should_end_window_at_nominal_time_when_no_previous_batch(current, fake_domain):
    # Arrange
    current.return_value.configure_mock(**fake_domain)
    current.return_value.nominal_time = CURRENT_START
    current.return_value.registries.batch.get_latest.return_value = None
    current.return_value.registries.batch.register.side_effect = lambda batch: batch

    # Act
    actual = Batch.acquire().state.end

    # Assert
    expected = CURRENT_START
    assert actual == expected


@patch("tiozin.api.context.Context.current")
def test_acquire_should_start_from_epoch_when_no_previous_batch(current, fake_domain):
    # Arrange
    current.return_value.configure_mock(**fake_domain)
    current.return_value.nominal_time = CURRENT_START
    current.return_value.registries.batch.get_latest.return_value = None
    current.return_value.registries.batch.register.side_effect = lambda batch: batch

    # Act
    actual = Batch.acquire().state.start

    # Assert
    expected = datetime(1970, 1, 1, tzinfo=UTC)
    assert actual == expected


@patch("tiozin.api.context.Context.current")
def test_acquire_should_start_watermarks_empty_when_no_previous_batch(current, fake_domain):
    # Arrange
    current.return_value.configure_mock(**fake_domain)
    current.return_value.nominal_time = CURRENT_START
    current.return_value.registries.batch.get_latest.return_value = None
    current.return_value.registries.batch.register.side_effect = lambda batch: batch

    # Act
    actual = Batch.acquire().state.watermarks

    # Assert
    expected = {}
    assert actual == expected
