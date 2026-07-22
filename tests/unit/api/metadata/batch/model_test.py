from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from tiozin import Batch, BatchStatus
from tiozin.api import Cadence
from tiozin.api.metadata.batch.exceptions import BatchTransitionError
from tiozin.api.metadata.batch.state import BatchState

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
def registry():
    mock = MagicMock()
    with patch("tiozin.api.metadata.batch.model.Batch._registry", return_value=mock):
        yield mock


@pytest.fixture
def context(fake_domain):
    context = MagicMock(
        **fake_domain,
        cadence=Cadence.MINUTELY,
        nominal_time=CURRENT_START,
    )
    context.registries.batch.register.side_effect = lambda batch: batch
    with patch("tiozin.api.context.Context.current", return_value=context):
        yield context


# ============================================================================
# construction / validation
# ============================================================================
def test_status_should_default_to_pending(fake_domain: dict):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    actual = batch.status

    # Assert
    expected = BatchStatus.PENDING
    assert actual == expected


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
        ("attempts", 3),
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
# computed properties - retries
# ============================================================================
@pytest.mark.parametrize(
    "attempts, expected_retries",
    [
        (0, 0),
        (1, 0),
        (2, 1),
        (3, 2),
    ],
)
def test_retries_should_count_attempts_beyond_the_first(
    attempts, expected_retries, fake_domain: dict
):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, attempts=attempts)

    # Act
    actual = batch.retries

    # Assert
    expected = expected_retries
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


# ============================================================================
# lifecycle - begin (delegation)
# ============================================================================
def test_begin_should_delegate_to_registry(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    batch.begin()

    # Assert
    registry.register_transition.assert_called_once_with(batch)


def test_begin_should_merge_attributes(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, attributes={"existing1": "value1"})

    # Act
    batch.begin(extra1="value2")

    # Assert
    actual = batch.attributes
    expected = {"existing1": "value1", "extra1": "value2"}
    assert actual == expected


def test_begin_should_return_registry_result(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    result = batch.begin()

    # Assert
    actual = result
    expected = registry.register_transition.return_value
    assert actual is expected


def test_begin_should_increment_attempts(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, attempts=2)

    # Act
    batch.begin()

    # Assert
    actual = batch.attempts
    expected = 3
    assert actual == expected


def test_begin_should_transition_status_to_running(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.PENDING)

    # Act
    batch.begin()

    # Assert
    actual = batch.status
    expected = BatchStatus.RUNNING
    assert actual == expected


def test_begin_should_raise_transition_error_when_transition_is_invalid(
    registry: MagicMock, fake_domain
):
    # Arrange
    registry.failfast = True
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.SUCCEEDED)

    # Act / Assert
    with pytest.raises(BatchTransitionError):
        batch.begin()


# ============================================================================
# lifecycle - commit (delegation)
# ============================================================================
def test_commit_should_delegate_to_registry(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.RUNNING)

    # Act
    batch.commit()

    # Assert
    registry.register_transition.assert_called_once_with(batch)


def test_commit_should_merge_attributes(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.RUNNING,
        attributes={"existing1": "value1"},
    )

    # Act
    batch.commit(extra1="value2")

    # Assert
    actual = batch.attributes
    expected = {"existing1": "value1", "extra1": "value2"}
    assert actual == expected


def test_commit_should_return_registry_result(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.RUNNING)

    # Act
    result = batch.commit()

    # Assert
    actual = result
    expected = registry.register_transition.return_value
    assert actual is expected


def test_commit_should_transition_status_to_succeeded(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.RUNNING)

    # Act
    batch.commit()

    # Assert
    actual = batch.status
    expected = BatchStatus.SUCCEEDED
    assert actual == expected


def test_commit_should_raise_transition_error_when_transition_is_invalid(
    registry: MagicMock, fake_domain
):
    # Arrange
    registry.failfast = True
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.PENDING)

    # Act / Assert
    with pytest.raises(BatchTransitionError):
        batch.commit()


# ============================================================================
# lifecycle - fail (delegation)
# ============================================================================
def test_rollback_should_delegate_to_registry(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.RUNNING)

    # Act
    batch.rollback()

    # Assert
    registry.register_transition.assert_called_once_with(batch)


def test_rollback_should_merge_attributes(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.RUNNING,
        attributes={"existing1": "value1"},
    )

    # Act
    batch.rollback(extra1="value2")

    # Assert
    actual = batch.attributes
    expected = {"existing1": "value1", "extra1": "value2"}
    assert actual == expected


def test_rollback_should_return_registry_result(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.RUNNING)

    # Act
    result = batch.rollback()

    # Assert
    actual = result
    expected = registry.register_transition.return_value
    assert actual is expected


def test_rollback_should_transition_status_to_failed(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.RUNNING)

    # Act
    batch.rollback()

    # Assert
    actual = batch.status
    expected = BatchStatus.FAILED
    assert actual == expected


# ============================================================================
# lifecycle - cancel (delegation)
# ============================================================================
def test_cancel_should_delegate_to_registry(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    batch.cancel()

    # Assert
    registry.register_transition.assert_called_once_with(batch)


def test_cancel_should_merge_attributes(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, attributes={"existing1": "value1"})

    # Act
    batch.cancel(extra1="value2")

    # Assert
    actual = batch.attributes
    expected = {"existing1": "value1", "extra1": "value2"}
    assert actual == expected


def test_cancel_should_return_registry_result(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    result = batch.cancel()

    # Assert
    actual = result
    expected = registry.register_transition.return_value
    assert actual is expected


def test_cancel_should_transition_status_to_canceled(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.PENDING)

    # Act
    batch.cancel()

    # Assert
    actual = batch.status
    expected = BatchStatus.CANCELED
    assert actual == expected


# ============================================================================
# lifecycle - quarantine (delegation)
# ============================================================================
def test_quarantine_should_delegate_to_registry(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.RUNNING)

    # Act
    batch.quarantine()

    # Assert
    registry.register_transition.assert_called_once_with(batch)


def test_quarantine_should_merge_attributes(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.RUNNING,
        attributes={"existing1": "value1"},
    )

    # Act
    batch.quarantine(extra1="value2")

    # Assert
    actual = batch.attributes
    expected = {"existing1": "value1", "extra1": "value2"}
    assert actual == expected


def test_quarantine_should_return_registry_result(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.RUNNING)

    # Act
    result = batch.quarantine()

    # Assert
    actual = result
    expected = registry.register_transition.return_value
    assert actual is expected


def test_quarantine_should_transition_status_to_quarantined(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.RUNNING)

    # Act
    batch.quarantine()

    # Assert
    actual = batch.status
    expected = BatchStatus.QUARANTINED
    assert actual == expected


# ============================================================================
# lifecycle - replay (delegation)
# ============================================================================
def test_replay_should_delegate_to_registry(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.SUCCEEDED)

    # Act
    batch.replay()

    # Assert
    registry.register_transition.assert_called_once_with(batch)


def test_replay_should_merge_attributes(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.SUCCEEDED,
        attributes={"existing1": "value1"},
    )

    # Act
    batch.replay(extra1="value2")

    # Assert
    actual = batch.attributes
    expected = {"existing1": "value1", "extra1": "value2"}
    assert actual == expected


def test_replay_should_return_registry_result(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.SUCCEEDED)

    # Act
    result = batch.replay()

    # Assert
    actual = result
    expected = registry.register_transition.return_value
    assert actual is expected


def test_replay_should_reset_attempts(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.SUCCEEDED,
        attempts=3,
    )

    # Act
    batch.replay()

    # Assert
    actual = batch.attempts
    expected = 0
    assert actual == expected


def test_replay_should_transition_status_to_pending(registry: MagicMock, fake_domain):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.SUCCEEDED)

    # Act
    batch.replay()

    # Assert
    actual = batch.status
    expected = BatchStatus.PENDING
    assert actual == expected


# ============================================================================
# lifecycle - transactional attributes (rollback / commit)
# ============================================================================
def test_commit_should_keep_attribute_mutations(job_context, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        attributes={"watermark": 10},
    )
    batch.begin()
    batch.attributes["watermark"] = 11
    batch.attributes["extra"] = 123456

    # Act
    batch.commit()

    # Assert
    actual = batch.attributes
    expected = {"watermark": 11, "extra": 123456}
    assert actual == expected


def test_rollback_should_discard_attribute_mutations(job_context, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        attributes={"watermark": 10},
    )
    batch.begin()
    batch.attributes["watermark"] = 11
    batch.attributes["extra"] = 123456

    # Act
    batch.rollback()

    # Assert
    actual = batch.attributes
    expected = {"watermark": 10}
    assert actual == expected


def test_rollback_should_discard_attributes_passed_to_begin(job_context, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        attributes={"a": 1},
    )
    batch.begin(extra="from_begin")

    # Act
    batch.rollback()

    # Assert
    actual = batch.attributes
    expected = {"a": 1}
    assert actual == expected


def test_rollback_should_reset_to_construction_attributes_when_begin_was_never_called(
    registry: MagicMock, fake_domain
):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.RUNNING,
        attributes={"watermark": 10},
    )
    batch.attributes["watermark"] = 99
    batch.attributes["extra"] = 123456

    # Act
    batch.rollback()

    # Assert
    actual = batch.attributes
    expected = {"watermark": 10}
    assert actual == expected


def test_rollback_should_set_error_message_in_attributes(job_context, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
    )
    batch.begin()

    # Act
    batch.rollback(error=RuntimeError("boom"))

    # Assert
    actual = batch.attributes["__error"]
    expected = "boom"
    assert actual == expected


def test_quarantine_should_keep_attribute_mutations(job_context, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        attributes={"watermark": 10},
    )
    batch.begin()
    batch.attributes["watermark"] = 11
    batch.attributes["extra"] = 123456

    # Act
    batch.quarantine()

    # Assert
    actual = batch.attributes
    expected = {"watermark": 11, "extra": 123456}
    assert actual == expected


def test_quarantine_should_set_error_message_in_attributes(job_context, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
    )
    batch.begin()

    # Act
    batch.quarantine(error=RuntimeError("boom"))

    # Assert
    actual = batch.attributes["__error"]
    expected = "boom"
    assert actual == expected


# ============================================================================
# acquire
# ============================================================================
def test_acquire_should_reuse_previous_batch_when_not_terminal(context, fake_domain):
    # Arrange
    previous = Batch(
        **fake_domain,
        nominal_time=PREVIOUS_START,
        status=BatchStatus.RUNNING,
    )
    context.registries.batch.get_latest.return_value = previous

    # Act
    actual = Batch.acquire()

    # Assert
    expected = previous
    assert actual is expected


def test_acquire_should_register_new_batch_when_previous_is_terminal(context, fake_domain):
    # Arrange
    previous = Batch(
        **fake_domain,
        nominal_time=PREVIOUS_START,
        status=BatchStatus.SUCCEEDED,
    )
    context.registries.batch.get_latest.return_value = previous

    # Act
    actual = Batch.acquire().nominal_time

    # Assert
    expected = CURRENT_START
    assert actual == expected


def test_acquire_should_carry_watermarks_forward_from_previous_state(context, fake_domain):
    # Arrange
    previous = Batch(
        **fake_domain,
        nominal_time=PREVIOUS_START,
        status=BatchStatus.SUCCEEDED,
        state=BatchState(watermarks={"orders": 42}),
    )
    context.registries.batch.get_latest.return_value = previous

    # Act
    actual = Batch.acquire().state.watermarks

    # Assert
    expected = {"orders": 42}
    assert actual == expected


def test_acquire_should_derive_window_from_previous_end(context, fake_domain):
    # Arrange
    context.nominal_time = CURRENT_NOMINAL_TIME

    previous = Batch(
        **fake_domain,
        nominal_time=PREVIOUS_START,
        status=BatchStatus.SUCCEEDED,
        state=BatchState(
            start=datetime(2026, 1, 14, tzinfo=UTC),
            end=PREVIOUS_END,
        ),
    )
    context.registries.batch.get_latest.return_value = previous

    # Act
    result = Batch.acquire().state

    # Assert
    actual = (result.start, result.end)
    expected = (
        PREVIOUS_END,
        CURRENT_NOMINAL_TIME,
    )
    assert actual == expected


def test_acquire_should_end_window_at_nominal_time_when_no_previous_batch(context):
    # Arrange
    context.registries.batch.get_latest.return_value = None

    # Act
    actual = Batch.acquire().state.end

    # Assert
    expected = CURRENT_START
    assert actual == expected


def test_acquire_should_start_from_epoch_when_no_previous_batch(context):
    # Arrange
    context.registries.batch.get_latest.return_value = None

    # Act
    actual = Batch.acquire().state.start

    # Assert
    expected = datetime(1970, 1, 1, tzinfo=UTC)
    assert actual == expected


def test_acquire_should_start_watermarks_empty_when_no_previous_batch(context):
    # Arrange
    context.registries.batch.get_latest.return_value = None

    # Act
    actual = Batch.acquire().state.watermarks

    # Assert
    expected = {}
    assert actual == expected
