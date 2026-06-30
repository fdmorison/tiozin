from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from tiozin.api.metadata.batch.model import Batch
from tiozin.api.metadata.batch.status import BatchStatus
from tiozin.exceptions.misc import ModelError

EXPLICIT_ID = "explicit-id-1234"


# ============================================================================
# construction / validation
# ============================================================================
def test_id_should_be_chronologically_sortable_when_not_provided(fake_domain: dict):
    # Arrange
    nominal_time = datetime(2026, 1, 15, tzinfo=UTC)

    # Act
    first = Batch(**fake_domain, nominal_time=nominal_time)
    second = Batch(**fake_domain, nominal_time=nominal_time)

    # Assert
    assert second.id > first.id


def test_id_should_be_preserved_when_provided(fake_domain: dict):
    # Arrange
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC), id=EXPLICIT_ID)

    # Act
    actual = state.id

    # Assert
    expected = EXPLICIT_ID
    assert actual == expected


def test_status_should_default_to_pending(fake_domain: dict):
    # Arrange
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    actual = state.status

    # Assert
    expected = BatchStatus.PENDING
    assert actual == expected


def test_failure_count_should_default_to_zero(fake_domain: dict):
    # Arrange
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    actual = state.failure_count

    # Assert
    expected = 0
    assert actual == expected


def test_attributes_should_default_to_empty_dict(fake_domain: dict):
    # Arrange
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    actual = state.attributes

    # Assert
    expected = {}
    assert actual == expected


def test_batch_should_raise_when_failure_count_is_negative(fake_domain: dict):
    # Act / Assert
    with pytest.raises(ModelError):
        Batch(
            **fake_domain,
            nominal_time=datetime(2026, 1, 15, tzinfo=UTC),
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
        ("nominal_time", datetime(2026, 2, 1, tzinfo=UTC)),
        ("created_at", datetime(2026, 2, 1, tzinfo=UTC)),
    ],
)
def test_batch_should_raise_when_frozen_field_is_reassigned(field, value, fake_domain: dict):
    # Arrange
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act / Assert
    with pytest.raises(ValidationError):
        setattr(state, field, value)


@pytest.mark.parametrize(
    "field, value",
    [
        ("status", BatchStatus.SUCCEEDED),
        ("failure_count", 3),
        ("attributes", {"extra1": "value1"}),
        ("updated_at", datetime(2026, 2, 1, tzinfo=UTC)),
    ],
)
def test_batch_should_reassign_when_mutable_field_is_set(field, value, fake_domain: dict):
    # Arrange
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    setattr(state, field, value)

    # Assert
    actual = getattr(state, field)
    expected = value
    assert actual == expected


# ============================================================================
# computed properties - keys
# ============================================================================
def test_domain_key_should_return_domain_fields():
    # Arrange
    state = Batch(
        org="acme",
        region="us-east",
        domain="sales",
        subdomain="orders",
        layer="bronze",
        product="catalog",
        model="products",
        nominal_time=datetime(2026, 1, 15, tzinfo=UTC),
    )

    # Act
    actual = state.domain_key

    # Assert
    expected = ("acme", "us-east", "sales", "orders")
    assert actual == expected


def test_product_key_should_return_product_fields():
    # Arrange
    state = Batch(
        org="acme",
        region="us-east",
        domain="sales",
        subdomain="orders",
        layer="bronze",
        product="catalog",
        model="products",
        nominal_time=datetime(2026, 1, 15, tzinfo=UTC),
    )

    # Act
    actual = state.product_key

    # Assert
    expected = ("bronze", "catalog", "products")
    assert actual == expected


def test_resource_key_should_return_domain_and_product_fields():
    # Arrange
    state = Batch(
        org="acme",
        region="us-east",
        domain="sales",
        subdomain="orders",
        layer="bronze",
        product="catalog",
        model="products",
        nominal_time=datetime(2026, 1, 15, tzinfo=UTC),
    )

    # Act
    actual = state.resource_key

    # Assert
    expected = ("acme", "us-east", "sales", "orders", "bronze", "catalog", "products")
    assert actual == expected


def test_natural_key_should_return_resource_fields_and_nominal_time():
    # Arrange
    state = Batch(
        org="acme",
        region="us-east",
        domain="sales",
        subdomain="orders",
        layer="bronze",
        product="catalog",
        model="products",
        nominal_time=datetime(2026, 1, 15, tzinfo=UTC),
    )

    # Act
    actual = state.natural_key

    # Assert
    expected = (
        "acme",
        "us-east",
        "sales",
        "orders",
        "bronze",
        "catalog",
        "products",
        datetime(2026, 1, 15, tzinfo=UTC).replace(second=0, microsecond=0).isoformat(),
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
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    state.register()

    # Assert
    registry.register.assert_called_once_with(state)


@patch("tiozin.api.context.Context.current")
def test_register_should_return_self(current, fake_domain):
    # Arrange
    current.return_value.registries.batch = MagicMock()
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    actual = state.register()

    # Assert
    assert actual is state


# ============================================================================
# lifecycle - begin
# ============================================================================
@patch("tiozin.api.context.Context.current")
def test_begin_should_delegate_to_registry(current, fake_domain):
    # Arrange
    registry = MagicMock()
    current.return_value.registries.batch = registry
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    state.begin(extra1="value1")

    # Assert
    registry.begin.assert_called_once_with(state)


@patch("tiozin.api.context.Context.current")
def test_begin_should_merge_attributes_into_state(current, fake_domain):
    # Arrange
    current.return_value.registries.batch = MagicMock()
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    state.begin(extra1="value1")

    # Assert
    actual = state.attributes
    expected = {"extra1": "value1"}
    assert actual == expected


@patch("tiozin.api.context.Context.current")
def test_begin_should_return_self(current, fake_domain):
    # Arrange
    current.return_value.registries.batch = MagicMock()
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    actual = state.begin()

    # Assert
    assert actual is state


# ============================================================================
# lifecycle - commit
# ============================================================================
@patch("tiozin.api.context.Context.current")
def test_commit_should_delegate_to_registry(current, fake_domain):
    # Arrange
    registry = MagicMock()
    current.return_value.registries.batch = registry
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    state.commit(extra1="value1")

    # Assert
    registry.commit.assert_called_once_with(state)


@patch("tiozin.api.context.Context.current")
def test_commit_should_merge_attributes_into_state(current, fake_domain):
    # Arrange
    current.return_value.registries.batch = MagicMock()
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    state.commit(extra1="value1")

    # Assert
    actual = state.attributes
    expected = {"extra1": "value1"}
    assert actual == expected


@patch("tiozin.api.context.Context.current")
def test_commit_should_return_self(current, fake_domain):
    # Arrange
    current.return_value.registries.batch = MagicMock()
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    actual = state.commit()

    # Assert
    assert actual is state


# ============================================================================
# lifecycle - fail
# ============================================================================
@patch("tiozin.api.metadata.batch.model.Batch._registry")
def test_fail_should_delegate_to_registry(registry: MagicMock, fake_domain):
    # Arrange
    registry.return_value.retries = 3
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    state.fail(extra1="value1")

    # Assert
    registry.return_value.fail.assert_called_once_with(state)


@patch("tiozin.api.metadata.batch.model.Batch._registry")
def test_fail_should_merge_attributes_into_state(registry: MagicMock, fake_domain):
    # Arrange
    registry.return_value.retries = 3
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    state.fail(extra1="value1")

    # Assert
    actual = state.attributes
    expected = {"extra1": "value1"}
    assert actual == expected


@patch("tiozin.api.metadata.batch.model.Batch._registry")
def test_fail_should_return_self(registry: MagicMock, fake_domain):
    # Arrange
    registry.return_value.retries = 3
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    actual = state.fail()

    # Assert
    assert actual is state


@patch("tiozin.api.context.Context.current")
def test_fail_should_increment_failure_count(current, fake_domain):
    # Arrange
    current.return_value.registries.batch = MagicMock()
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    state.fail()

    # Assert
    actual = state.failure_count
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
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    state.cancel(extra1="value1")

    # Assert
    registry.cancel.assert_called_once_with(state)


@patch("tiozin.api.context.Context.current")
def test_cancel_should_merge_attributes_into_state(current, fake_domain):
    # Arrange
    current.return_value.registries.batch = MagicMock()
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    state.cancel(extra1="value1")

    # Assert
    actual = state.attributes
    expected = {"extra1": "value1"}
    assert actual == expected


@patch("tiozin.api.context.Context.current")
def test_cancel_should_return_self(current, fake_domain):
    # Arrange
    current.return_value.registries.batch = MagicMock()
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    actual = state.cancel()

    # Assert
    assert actual is state


# ============================================================================
# lifecycle - quarantine
# ============================================================================
@patch("tiozin.api.context.Context.current")
def test_quarantine_should_delegate_to_registry(current, fake_domain):
    # Arrange
    registry = MagicMock()
    current.return_value.registries.batch = registry
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    state.quarantine(extra1="value1")

    # Assert
    registry.quarantine.assert_called_once_with(state)


@patch("tiozin.api.context.Context.current")
def test_quarantine_should_merge_attributes_into_state(current, fake_domain):
    # Arrange
    current.return_value.registries.batch = MagicMock()
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    state.quarantine(extra1="value1")

    # Assert
    actual = state.attributes
    expected = {"extra1": "value1"}
    assert actual == expected


@patch("tiozin.api.context.Context.current")
def test_quarantine_should_return_self(current, fake_domain):
    # Arrange
    current.return_value.registries.batch = MagicMock()
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    actual = state.quarantine()

    # Assert
    assert actual is state


# ============================================================================
# lifecycle - replay
# ============================================================================
@patch("tiozin.api.context.Context.current")
def test_replay_should_delegate_to_registry(current, fake_domain):
    # Arrange
    registry = MagicMock()
    current.return_value.registries.batch = registry
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    state.replay(extra1="value1")

    # Assert
    registry.replay.assert_called_once_with(state)


@patch("tiozin.api.context.Context.current")
def test_replay_should_merge_attributes_into_state(current, fake_domain):
    # Arrange
    current.return_value.registries.batch = MagicMock()
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    state.replay(extra1="value1")

    # Assert
    actual = state.attributes
    expected = {"extra1": "value1"}
    assert actual == expected


@patch("tiozin.api.context.Context.current")
def test_replay_should_return_self(current, fake_domain):
    # Arrange
    current.return_value.registries.batch = MagicMock()
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC))

    # Act
    actual = state.replay()

    # Assert
    assert actual is state


@patch("tiozin.api.context.Context.current")
def test_replay_should_reset_failure_count(current, fake_domain):
    # Arrange
    current.return_value.registries.batch = MagicMock()
    state = Batch(**fake_domain, nominal_time=datetime(2026, 1, 15, tzinfo=UTC), failure_count=3)

    # Act
    state.replay()

    # Assert
    actual = state.failure_count
    expected = 0
    assert actual == expected
