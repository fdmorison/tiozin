from datetime import UTC, datetime
from unittest.mock import MagicMock, call, patch

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

# Stale timestamp for asserting that a no-op verb preserves updated_at.
OLD_UPDATED_AT = datetime(2026, 1, 1, tzinfo=UTC)

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


def test_begin_should_not_persist_when_already_running(registry: MagicMock, fake_domain):
    # Arrange
    registry.failfast = False
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.RUNNING)

    # Act
    batch.begin()

    # Assert
    registry.register_transition.assert_not_called()


def test_begin_should_not_increment_attempts_when_already_running(registry: MagicMock, fake_domain):
    # Arrange
    registry.failfast = False
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.RUNNING,
        attempts=2,
    )

    # Act
    batch.begin()

    # Assert
    actual = batch.attempts
    expected = 2
    assert actual == expected


@patch("tiozin.api.metadata.batch.model.logger")
def test_begin_should_warn_when_already_running(
    logger: MagicMock, registry: MagicMock, fake_domain
):
    # Arrange
    registry.failfast = False
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.RUNNING)

    # Act
    batch.begin()

    # Assert
    actual = logger.warning.call_args
    expected = call("Cannot begin a batch that is already running.")
    assert actual == expected


def test_begin_should_keep_updated_at_when_already_running(registry: MagicMock, fake_domain):
    # Arrange
    registry.failfast = False
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.RUNNING,
        updated_at=OLD_UPDATED_AT,
    )

    # Act
    batch.begin()

    # Assert
    actual = batch.updated_at
    expected = OLD_UPDATED_AT
    assert actual == expected


def test_begin_should_raise_transition_error_when_already_running(registry: MagicMock, fake_domain):
    # Arrange
    registry.failfast = True
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.RUNNING)

    # Act / Assert
    with pytest.raises(BatchTransitionError):
        batch.begin()


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


def test_commit_should_not_persist_when_already_succeeded(registry: MagicMock, fake_domain):
    # Arrange
    registry.failfast = False
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.SUCCEEDED)

    # Act
    batch.commit()

    # Assert
    registry.register_transition.assert_not_called()


@patch("tiozin.api.metadata.batch.model.logger")
def test_commit_should_warn_when_already_succeeded(
    logger: MagicMock, registry: MagicMock, fake_domain
):
    # Arrange
    registry.failfast = False
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.SUCCEEDED)

    # Act
    batch.commit()

    # Assert
    actual = logger.warning.call_args
    expected = call("Cannot commit a batch that has already succeeded.")
    assert actual == expected


def test_commit_should_keep_updated_at_when_already_succeeded(registry: MagicMock, fake_domain):
    # Arrange
    registry.failfast = False
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.SUCCEEDED,
        updated_at=OLD_UPDATED_AT,
    )

    # Act
    batch.commit()

    # Assert
    actual = batch.updated_at
    expected = OLD_UPDATED_AT
    assert actual == expected


def test_commit_should_raise_transition_error_when_already_succeeded(
    registry: MagicMock, fake_domain
):
    # Arrange
    registry.failfast = True
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.SUCCEEDED)

    # Act / Assert
    with pytest.raises(BatchTransitionError):
        batch.commit()


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


def test_rollback_should_not_persist_when_already_failed(registry: MagicMock, fake_domain):
    # Arrange
    registry.failfast = False
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.FAILED)

    # Act
    batch.rollback()

    # Assert
    registry.register_transition.assert_not_called()


@patch("tiozin.api.metadata.batch.model.logger")
def test_rollback_should_warn_when_already_failed(
    logger: MagicMock, registry: MagicMock, fake_domain
):
    # Arrange
    registry.failfast = False
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.FAILED)

    # Act
    batch.rollback()

    # Assert
    actual = logger.warning.call_args
    expected = call("Cannot rollback a batch that has already failed.")
    assert actual == expected


def test_rollback_should_keep_updated_at_when_already_failed(registry: MagicMock, fake_domain):
    # Arrange
    registry.failfast = False
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.FAILED,
        updated_at=OLD_UPDATED_AT,
    )

    # Act
    batch.rollback()

    # Assert
    actual = batch.updated_at
    expected = OLD_UPDATED_AT
    assert actual == expected


def test_rollback_should_raise_transition_error_when_already_failed(
    registry: MagicMock, fake_domain
):
    # Arrange
    registry.failfast = True
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.FAILED)

    # Act / Assert
    with pytest.raises(BatchTransitionError):
        batch.rollback()


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


def test_cancel_should_not_persist_when_already_canceled(registry: MagicMock, fake_domain):
    # Arrange
    registry.failfast = False
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.CANCELED)

    # Act
    batch.cancel()

    # Assert
    registry.register_transition.assert_not_called()


@patch("tiozin.api.metadata.batch.model.logger")
def test_cancel_should_warn_when_already_canceled(
    logger: MagicMock, registry: MagicMock, fake_domain
):
    # Arrange
    registry.failfast = False
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.CANCELED)

    # Act
    batch.cancel()

    # Assert
    actual = logger.warning.call_args
    expected = call("Cannot cancel a batch that has already been canceled.")
    assert actual == expected


def test_cancel_should_keep_updated_at_when_already_canceled(registry: MagicMock, fake_domain):
    # Arrange
    registry.failfast = False
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.CANCELED,
        updated_at=OLD_UPDATED_AT,
    )

    # Act
    batch.cancel()

    # Assert
    actual = batch.updated_at
    expected = OLD_UPDATED_AT
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


def test_quarantine_should_not_persist_when_already_quarantined(registry: MagicMock, fake_domain):
    # Arrange
    registry.failfast = False
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.QUARANTINED)

    # Act
    batch.quarantine()

    # Assert
    registry.register_transition.assert_not_called()


@patch("tiozin.api.metadata.batch.model.logger")
def test_quarantine_should_warn_when_already_quarantined(
    logger: MagicMock, registry: MagicMock, fake_domain
):
    # Arrange
    registry.failfast = False
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.QUARANTINED)

    # Act
    batch.quarantine()

    # Assert
    actual = logger.warning.call_args
    expected = call("Cannot quarantine a batch that has already been quarantined.")
    assert actual == expected


def test_quarantine_should_keep_updated_at_when_already_quarantined(
    registry: MagicMock, fake_domain
):
    # Arrange
    registry.failfast = False
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.QUARANTINED,
        updated_at=OLD_UPDATED_AT,
    )

    # Act
    batch.quarantine()

    # Assert
    actual = batch.updated_at
    expected = OLD_UPDATED_AT
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


def test_replay_should_not_persist_when_already_pending(registry: MagicMock, fake_domain):
    # Arrange
    registry.failfast = False
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.PENDING)

    # Act
    batch.replay()

    # Assert
    registry.register_transition.assert_not_called()


@patch("tiozin.api.metadata.batch.model.logger")
def test_replay_should_warn_when_already_pending(
    logger: MagicMock, registry: MagicMock, fake_domain
):
    # Arrange
    registry.failfast = False
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME, status=BatchStatus.PENDING)

    # Act
    batch.replay()

    # Assert
    actual = logger.warning.call_args
    expected = call("Cannot replay a batch that is already pending.")
    assert actual == expected


def test_replay_should_keep_updated_at_when_already_pending(registry: MagicMock, fake_domain):
    # Arrange
    registry.failfast = False
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=BatchStatus.PENDING,
        updated_at=OLD_UPDATED_AT,
    )

    # Act
    batch.replay()

    # Assert
    actual = batch.updated_at
    expected = OLD_UPDATED_AT
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
