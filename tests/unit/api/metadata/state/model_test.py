from datetime import UTC, date, datetime
from unittest.mock import MagicMock, patch

import pytest

from tiozin.api.metadata.state.model import State
from tiozin.api.metadata.state.status import BatchStatus
from tiozin.exceptions.misc import ModelError

DERIVED_ID = "65e51fad-4c65-5db7-b6a1-7849974e0d39"
EXPLICIT_ID = "explicit-id-1234"


# ============================================================================
# construction / validation
# ============================================================================
def test_id_should_be_derived_from_natural_key_when_not_provided():
    # Arrange
    state = State(
        org="acme",
        region="us-east",
        domain="sales",
        subdomain="orders",
        layer="bronze",
        product="catalog",
        model="products",
        batch_key="2026-01-15",
    )

    # Act
    actual = state.id

    # Assert
    expected = DERIVED_ID
    assert actual == expected


def test_id_should_be_preserved_when_provided(fake_domain: dict):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15", id=EXPLICIT_ID)

    # Act
    actual = state.id

    # Assert
    expected = EXPLICIT_ID
    assert actual == expected


def test_status_should_default_to_pending(fake_domain: dict):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    actual = state.status

    # Assert
    expected = BatchStatus.PENDING
    assert actual == expected


def test_failure_count_should_default_to_zero(fake_domain: dict):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    actual = state.failure_count

    # Assert
    expected = 0
    assert actual == expected


def test_attributes_should_default_to_empty_dict(fake_domain: dict):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    actual = state.attributes

    # Assert
    expected = {}
    assert actual == expected


def test_state_should_raise_when_failure_count_is_negative(fake_domain: dict):
    # Act / Assert
    with pytest.raises(ModelError):
        State(**fake_domain, batch_key="2026-01-15", failure_count=-1)


# ============================================================================
# computed properties - keys
# ============================================================================
def test_domain_key_should_return_domain_fields():
    # Arrange
    state = State(
        org="acme",
        region="us-east",
        domain="sales",
        subdomain="orders",
        layer="bronze",
        product="catalog",
        model="products",
        batch_key="2026-01-15",
    )

    # Act
    actual = state.domain_key

    # Assert
    expected = ("acme", "us-east", "sales", "orders")
    assert actual == expected


def test_product_key_should_return_product_fields():
    # Arrange
    state = State(
        org="acme",
        region="us-east",
        domain="sales",
        subdomain="orders",
        layer="bronze",
        product="catalog",
        model="products",
        batch_key="2026-01-15",
    )

    # Act
    actual = state.product_key

    # Assert
    expected = ("bronze", "catalog", "products")
    assert actual == expected


def test_resource_key_should_return_domain_and_product_fields():
    # Arrange
    state = State(
        org="acme",
        region="us-east",
        domain="sales",
        subdomain="orders",
        layer="bronze",
        product="catalog",
        model="products",
        batch_key="2026-01-15",
    )

    # Act
    actual = state.resource_key

    # Assert
    expected = ("acme", "us-east", "sales", "orders", "bronze", "catalog", "products")
    assert actual == expected


def test_natural_key_should_return_resource_fields_and_batch_key():
    # Arrange
    state = State(
        org="acme",
        region="us-east",
        domain="sales",
        subdomain="orders",
        layer="bronze",
        product="catalog",
        model="products",
        batch_key="2026-01-15",
    )

    # Act
    actual = state.natural_key

    # Assert
    expected = ("acme", "us-east", "sales", "orders", "bronze", "catalog", "products", "2026-01-15")
    assert actual == expected


# ============================================================================
# computed properties - batch_date
# ============================================================================
def test_batch_date_should_parse_batch_key_as_date(fake_domain: dict):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    actual = state.batch_date

    # Assert
    expected = date(2026, 1, 15)
    assert actual == expected


def test_batch_date_setter_should_store_date_as_isoformat(fake_domain: dict):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    state.batch_date = date(2026, 1, 15)

    # Assert
    actual = state.batch_key
    expected = "2026-01-15"
    assert actual == expected


def test_batch_date_setter_should_store_date_part_when_given_datetime(fake_domain: dict):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    state.batch_date = datetime(2026, 1, 15, 10, 30, 0, tzinfo=UTC)

    # Assert
    actual = state.batch_key
    expected = "2026-01-15"
    assert actual == expected


# ============================================================================
# computed properties - batch_timestamp
# ============================================================================
def test_batch_timestamp_should_parse_batch_key_as_datetime(fake_domain: dict):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15T10:30:00+00:00")

    # Act
    actual = state.batch_timestamp

    # Assert
    expected = datetime(2026, 1, 15, 10, 30, 0, tzinfo=UTC)
    assert actual == expected


def test_batch_timestamp_setter_should_store_datetime_as_isoformat(fake_domain: dict):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    state.batch_timestamp = datetime(2026, 1, 15, 10, 30, 0, tzinfo=UTC)

    # Assert
    actual = state.batch_key
    expected = "2026-01-15T10:30:00+00:00"
    assert actual == expected


def test_batch_timestamp_setter_should_store_utc_midnight_when_given_date(fake_domain: dict):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    state.batch_timestamp = date(2026, 1, 15)

    # Assert
    actual = state.batch_key
    expected = "2026-01-15T00:00:00+00:00"
    assert actual == expected


# ============================================================================
# computed properties - batch_int
# ============================================================================
def test_batch_int_should_parse_batch_key_as_int(fake_domain: dict):
    # Arrange
    state = State(**fake_domain, batch_key="20260115")

    # Act
    actual = state.batch_int

    # Assert
    expected = 20260115
    assert actual == expected


def test_batch_int_setter_should_store_int_as_string(fake_domain: dict):
    # Arrange
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    state.batch_int = 20260115

    # Assert
    actual = state.batch_key
    expected = "20260115"
    assert actual == expected


# ============================================================================
# lifecycle - persist
# ============================================================================
@patch("tiozin.api.context.Context.current")
def test_register_should_delegate_to_registry(current, fake_domain):
    # Arrange
    registry = MagicMock()
    current.return_value.registries.state = registry
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    state.register()

    # Assert
    registry.register.assert_called_once_with(state)


@patch("tiozin.api.context.Context.current")
def test_register_should_return_self(current, fake_domain):
    # Arrange
    current.return_value.registries.state = MagicMock()
    state = State(**fake_domain, batch_key="2026-01-15")

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
    current.return_value.registries.state = registry
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    state.begin(extra1="value1")

    # Assert
    registry.begin.assert_called_once_with(state)


@patch("tiozin.api.context.Context.current")
def test_begin_should_merge_attributes_into_state(current, fake_domain):
    # Arrange
    current.return_value.registries.state = MagicMock()
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    state.begin(extra1="value1")

    # Assert
    actual = state.attributes
    expected = {"extra1": "value1"}
    assert actual == expected


@patch("tiozin.api.context.Context.current")
def test_begin_should_return_self(current, fake_domain):
    # Arrange
    current.return_value.registries.state = MagicMock()
    state = State(**fake_domain, batch_key="2026-01-15")

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
    current.return_value.registries.state = registry
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    state.commit(extra1="value1")

    # Assert
    registry.commit.assert_called_once_with(state)


@patch("tiozin.api.context.Context.current")
def test_commit_should_merge_attributes_into_state(current, fake_domain):
    # Arrange
    current.return_value.registries.state = MagicMock()
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    state.commit(extra1="value1")

    # Assert
    actual = state.attributes
    expected = {"extra1": "value1"}
    assert actual == expected


@patch("tiozin.api.context.Context.current")
def test_commit_should_return_self(current, fake_domain):
    # Arrange
    current.return_value.registries.state = MagicMock()
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    actual = state.commit()

    # Assert
    assert actual is state


# ============================================================================
# lifecycle - fail
# ============================================================================
@patch("tiozin.api.metadata.state.model.State._registry")
def test_fail_should_delegate_to_registry(registry: MagicMock, fake_domain):
    # Arrange
    registry.return_value.retries = 3
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    state.fail(extra1="value1")

    # Assert
    registry.return_value.fail.assert_called_once_with(state)


@patch("tiozin.api.metadata.state.model.State._registry")
def test_fail_should_merge_attributes_into_state(registry: MagicMock, fake_domain):
    # Arrange
    registry.return_value.retries = 3
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    state.fail(extra1="value1")

    # Assert
    actual = state.attributes
    expected = {"extra1": "value1"}
    assert actual == expected


@patch("tiozin.api.metadata.state.model.State._registry")
def test_fail_should_return_self(registry: MagicMock, fake_domain):
    # Arrange
    registry.return_value.retries = 3
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    actual = state.fail()

    # Assert
    assert actual is state


@patch("tiozin.api.context.Context.current")
def test_fail_should_increment_failure_count(current, fake_domain):
    # Arrange
    current.return_value.registries.state = MagicMock()
    state = State(**fake_domain, batch_key="2026-01-15")

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
    current.return_value.registries.state = registry
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    state.cancel(extra1="value1")

    # Assert
    registry.cancel.assert_called_once_with(state)


@patch("tiozin.api.context.Context.current")
def test_cancel_should_merge_attributes_into_state(current, fake_domain):
    # Arrange
    current.return_value.registries.state = MagicMock()
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    state.cancel(extra1="value1")

    # Assert
    actual = state.attributes
    expected = {"extra1": "value1"}
    assert actual == expected


@patch("tiozin.api.context.Context.current")
def test_cancel_should_return_self(current, fake_domain):
    # Arrange
    current.return_value.registries.state = MagicMock()
    state = State(**fake_domain, batch_key="2026-01-15")

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
    current.return_value.registries.state = registry
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    state.quarantine(extra1="value1")

    # Assert
    registry.quarantine.assert_called_once_with(state)


@patch("tiozin.api.context.Context.current")
def test_quarantine_should_merge_attributes_into_state(current, fake_domain):
    # Arrange
    current.return_value.registries.state = MagicMock()
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    state.quarantine(extra1="value1")

    # Assert
    actual = state.attributes
    expected = {"extra1": "value1"}
    assert actual == expected


@patch("tiozin.api.context.Context.current")
def test_quarantine_should_return_self(current, fake_domain):
    # Arrange
    current.return_value.registries.state = MagicMock()
    state = State(**fake_domain, batch_key="2026-01-15")

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
    current.return_value.registries.state = registry
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    state.replay(extra1="value1")

    # Assert
    registry.replay.assert_called_once_with(state)


@patch("tiozin.api.context.Context.current")
def test_replay_should_merge_attributes_into_state(current, fake_domain):
    # Arrange
    current.return_value.registries.state = MagicMock()
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    state.replay(extra1="value1")

    # Assert
    actual = state.attributes
    expected = {"extra1": "value1"}
    assert actual == expected


@patch("tiozin.api.context.Context.current")
def test_replay_should_return_self(current, fake_domain):
    # Arrange
    current.return_value.registries.state = MagicMock()
    state = State(**fake_domain, batch_key="2026-01-15")

    # Act
    actual = state.replay()

    # Assert
    assert actual is state


@patch("tiozin.api.context.Context.current")
def test_replay_should_reset_failure_count(current, fake_domain):
    # Arrange
    current.return_value.registries.state = MagicMock()
    state = State(**fake_domain, batch_key="2026-01-15", failure_count=3)

    # Act
    state.replay()

    # Assert
    actual = state.failure_count
    expected = 0
    assert actual == expected
