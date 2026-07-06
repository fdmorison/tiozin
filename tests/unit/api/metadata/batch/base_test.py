from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from tiozin.api.metadata.batch.base import Batch
from tiozin.api.metadata.batch.state import BatchState
from tiozin.api.metadata.batch.status import BatchStatus
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
def test_domain_key_should_return_domain_fields():
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
    actual = batch.domain_key

    # Assert
    expected = ("acme", "us-east", "sales", "orders")
    assert actual == expected


def test_product_key_should_return_product_fields():
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
    actual = batch.product_key

    # Assert
    expected = ("bronze", "catalog", "products")
    assert actual == expected


def test_resource_key_should_return_domain_and_product_fields():
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
    actual = batch.resource_key

    # Assert
    expected = ("acme", "us-east", "sales", "orders", "bronze", "catalog", "products")
    assert actual == expected


def test_natural_key_should_return_resource_fields_and_nominal_time():
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
    actual = batch.natural_key

    # Assert
    expected = (
        "acme",
        "us-east",
        "sales",
        "orders",
        "bronze",
        "catalog",
        "products",
        NOMINAL_TIME.replace(second=0, microsecond=0).isoformat(),
    )
    assert actual == expected


# ============================================================================
# lifecycle - persist
# ============================================================================
@patch("tiozin.api.context.Context.current")
def test_register_should_delegate_to_registry(current, fake_domain):
    # Arrange
    registry = MagicMock()
    current.return_value.registries.batch = registry
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    batch.register()

    # Assert
    registry.register.assert_called_once_with(batch)


@patch("tiozin.api.context.Context.current")
def test_register_should_return_self(current, fake_domain):
    # Arrange
    current.return_value.registries.batch = MagicMock()
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    actual = batch.register()

    # Assert
    assert actual is batch


# ============================================================================
# lifecycle - begin
# ============================================================================
@patch("tiozin.api.context.Context.current")
def test_begin_should_delegate_to_registry(current, fake_domain):
    # Arrange
    registry = MagicMock()
    current.return_value.registries.batch = registry
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    batch.begin(extra1="value1")

    # Assert
    registry.begin.assert_called_once_with(batch)


@patch("tiozin.api.context.Context.current")
def test_begin_should_merge_attributes_into_state(current, fake_domain):
    # Arrange
    current.return_value.registries.batch = MagicMock()
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    batch.begin(extra1="value1")

    # Assert
    actual = batch.attributes
    expected = {"extra1": "value1"}
    assert actual == expected


@patch("tiozin.api.context.Context.current")
def test_begin_should_return_self(current, fake_domain):
    # Arrange
    current.return_value.registries.batch = MagicMock()
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    actual = batch.begin()

    # Assert
    assert actual is batch


# ============================================================================
# lifecycle - commit
# ============================================================================
@patch("tiozin.api.context.Context.current")
def test_commit_should_delegate_to_registry(current, fake_domain):
    # Arrange
    registry = MagicMock()
    current.return_value.registries.batch = registry
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    batch.commit(extra1="value1")

    # Assert
    registry.commit.assert_called_once_with(batch)


@patch("tiozin.api.context.Context.current")
def test_commit_should_merge_attributes_into_state(current, fake_domain):
    # Arrange
    current.return_value.registries.batch = MagicMock()
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    batch.commit(extra1="value1")

    # Assert
    actual = batch.attributes
    expected = {"extra1": "value1"}
    assert actual == expected


@patch("tiozin.api.context.Context.current")
def test_commit_should_return_self(current, fake_domain):
    # Arrange
    current.return_value.registries.batch = MagicMock()
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    actual = batch.commit()

    # Assert
    assert actual is batch


# ============================================================================
# lifecycle - fail
# ============================================================================
@patch("tiozin.api.metadata.batch.base.Batch._registry")
def test_fail_should_delegate_to_registry(registry: MagicMock, fake_domain):
    # Arrange
    registry.return_value.retries = 3
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    batch.fail(extra1="value1")

    # Assert
    registry.return_value.fail.assert_called_once_with(batch)


@patch("tiozin.api.metadata.batch.base.Batch._registry")
def test_fail_should_merge_attributes_into_batch(registry: MagicMock, fake_domain):
    # Arrange
    registry.return_value.retries = 3
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    batch.fail(extra1="value1")

    # Assert
    actual = batch.attributes
    expected = {"extra1": "value1"}
    assert actual == expected


@patch("tiozin.api.metadata.batch.base.Batch._registry")
def test_fail_should_return_self(registry: MagicMock, fake_domain):
    # Arrange
    registry.return_value.retries = 3
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    actual = batch.fail()

    # Assert
    assert actual is batch


@patch("tiozin.api.context.Context.current")
def test_fail_should_increment_failure_count(current, fake_domain):
    # Arrange
    current.return_value.registries.batch = MagicMock()
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    batch.fail()

    # Assert
    actual = batch.failure_count
    expected = 1
    assert actual == expected


# ============================================================================
# lifecycle - cancel
# ============================================================================
@patch("tiozin.api.context.Context.current")
def test_cancel_should_delegate_to_registry(current, fake_domain):
    # Arrange
    registry = MagicMock()
    current.return_value.registries.batch = registry
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    batch.cancel(extra1="value1")

    # Assert
    registry.cancel.assert_called_once_with(batch)


@patch("tiozin.api.context.Context.current")
def test_cancel_should_merge_attributes_into_state(current, fake_domain):
    # Arrange
    current.return_value.registries.batch = MagicMock()
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    batch.cancel(extra1="value1")

    # Assert
    actual = batch.attributes
    expected = {"extra1": "value1"}
    assert actual == expected


@patch("tiozin.api.context.Context.current")
def test_cancel_should_return_self(current, fake_domain):
    # Arrange
    current.return_value.registries.batch = MagicMock()
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    actual = batch.cancel()

    # Assert
    assert actual is batch


# ============================================================================
# lifecycle - quarantine
# ============================================================================
@patch("tiozin.api.context.Context.current")
def test_quarantine_should_delegate_to_registry(current, fake_domain):
    # Arrange
    registry = MagicMock()
    current.return_value.registries.batch = registry
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    batch.quarantine(extra1="value1")

    # Assert
    registry.quarantine.assert_called_once_with(batch)


@patch("tiozin.api.context.Context.current")
def test_quarantine_should_merge_attributes_into_state(current, fake_domain):
    # Arrange
    current.return_value.registries.batch = MagicMock()
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    batch.quarantine(extra1="value1")

    # Assert
    actual = batch.attributes
    expected = {"extra1": "value1"}
    assert actual == expected


@patch("tiozin.api.context.Context.current")
def test_quarantine_should_return_self(current, fake_domain):
    # Arrange
    current.return_value.registries.batch = MagicMock()
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    actual = batch.quarantine()

    # Assert
    assert actual is batch


# ============================================================================
# lifecycle - replay
# ============================================================================
@patch("tiozin.api.context.Context.current")
def test_replay_should_delegate_to_registry(current, fake_domain):
    # Arrange
    registry = MagicMock()
    current.return_value.registries.batch = registry
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    batch.replay(extra1="value1")

    # Assert
    registry.replay.assert_called_once_with(batch)


@patch("tiozin.api.context.Context.current")
def test_replay_should_merge_attributes_into_state(current, fake_domain):
    # Arrange
    current.return_value.registries.batch = MagicMock()
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    batch.replay(extra1="value1")

    # Assert
    actual = batch.attributes
    expected = {"extra1": "value1"}
    assert actual == expected


@patch("tiozin.api.context.Context.current")
def test_replay_should_return_self(current, fake_domain):
    # Arrange
    current.return_value.registries.batch = MagicMock()
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    actual = batch.replay()

    # Assert
    assert actual is batch


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

    # Act
    actual = Batch.acquire().nominal_time

    # Assert
    expected = CURRENT_START
    assert actual == expected


@patch("tiozin.api.context.Context.current")
def test_acquire_should_carry_watermark_forward_from_previous_state(current, fake_domain):
    # Arrange
    previous = Batch(
        **fake_domain,
        nominal_time=PREVIOUS_START,
        status=BatchStatus.SUCCEEDED,
        state=BatchState(watermark=42),
    )
    current.return_value.configure_mock(**fake_domain)
    current.return_value.nominal_time = CURRENT_START
    current.return_value.registries.batch.get_latest.return_value = previous

    # Act
    actual = Batch.acquire().state.watermark

    # Assert
    expected = 42
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

    # Act
    actual = Batch.acquire().state.start

    # Assert
    expected = datetime(1970, 1, 1, tzinfo=UTC)
    assert actual == expected


@patch("tiozin.api.context.Context.current")
def test_acquire_should_start_watermark_at_epoch_when_no_previous_batch(current, fake_domain):
    # Arrange
    current.return_value.configure_mock(**fake_domain)
    current.return_value.nominal_time = CURRENT_START
    current.return_value.registries.batch.get_latest.return_value = None

    # Act
    actual = Batch.acquire().state.watermark

    # Assert
    expected = datetime(1970, 1, 1, tzinfo=UTC)
    assert actual == expected
