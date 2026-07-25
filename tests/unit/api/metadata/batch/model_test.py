from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from freezegun import freeze_time
from pydantic import ValidationError

from tiozin import Batch, BatchStatus, config

# Default nominal_time for a test batch, and the value reassignment tests
# attempt to set on frozen/mutable fields.
NOMINAL_TIME = datetime(2026, 1, 15, tzinfo=UTC)
REASSIGNED_TIME = datetime(2026, 2, 1, tzinfo=UTC)

# Frozen clock used to assert the default of nominal_end_time (utcnow, truncated).
FROZEN_NOW = datetime(2026, 6, 1, 12, 30, tzinfo=UTC)


@pytest.fixture
def registry():
    mock = MagicMock()
    with patch("tiozin.api.metadata.batch.model.Batch._registry", return_value=mock):
        yield mock


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


@pytest.mark.parametrize("field", ["attributes", "bookmarks"])
def test_batch_should_default_metadata_map_to_empty_dict(field, fake_domain: dict):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    actual = getattr(batch, field)

    # Assert
    expected = {}
    assert actual == expected


def test_framework_should_default_to_app_identifier(fake_domain: dict):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    actual = batch.framework

    # Assert
    expected = config.app_identifier
    assert actual == expected


def test_framework_should_not_overwrite_explicit_value(fake_domain: dict):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        framework="some-old-framework/1.0.0",
    )

    # Act
    actual = batch.framework

    # Assert
    expected = "some-old-framework/1.0.0"
    assert actual == expected


# ============================================================================
# nominal window
# ============================================================================
def test_nominal_start_time_should_default_to_epoch(fake_domain: dict):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    actual = batch.nominal_start_time

    # Assert
    expected = datetime(1970, 1, 1, tzinfo=UTC)
    assert actual == expected


@freeze_time(FROZEN_NOW)
def test_nominal_end_time_should_default_to_current_time(fake_domain: dict):
    # Arrange
    batch = Batch(**fake_domain, nominal_time=NOMINAL_TIME)

    # Act
    actual = batch.nominal_end_time

    # Assert
    expected = FROZEN_NOW
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
        ("nominal_start_time", REASSIGNED_TIME),
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
        ("bookmarks", {"cursor1": "value1"}),
        ("nominal_end_time", REASSIGNED_TIME),
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


def test_replay_should_reset_attempts_when_batch_is_terminal(registry: MagicMock, fake_domain):
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


@pytest.mark.parametrize("status", [BatchStatus.RUNNING, BatchStatus.FAILED])
def test_replay_should_preserve_attempts_when_batch_is_operational(
    status, registry: MagicMock, fake_domain
):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        status=status,
        attempts=3,
    )

    # Act
    batch.replay()

    # Assert
    actual = batch.attempts
    expected = 3
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


def test_rollback_should_restore_bookmarks(job_context, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        bookmarks={"cursor": 10},
    )
    batch.begin()
    batch.bookmarks["cursor"] = 11
    batch.bookmarks["extra"] = 123456

    # Act
    batch.rollback()

    # Assert
    actual = batch.bookmarks
    expected = {"cursor": 10}
    assert actual == expected


def test_commit_should_keep_bookmark_mutations(job_context, fake_domain):
    # Arrange
    batch = Batch(
        **fake_domain,
        nominal_time=NOMINAL_TIME,
        bookmarks={"cursor": 10},
    )
    batch.begin()
    batch.bookmarks["cursor"] = 11
    batch.bookmarks["extra"] = 123456

    # Act
    batch.commit()

    # Assert
    actual = batch.bookmarks
    expected = {"cursor": 11, "extra": 123456}
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
