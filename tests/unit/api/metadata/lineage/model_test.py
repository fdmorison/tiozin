import pendulum
import pytest

from tests import config
from tiozin.api.metadata.lineage.model import (
    LineageRunEvent,
    LineageRunEventType,
)
from tiozin.api.runtime.context import Context

# ============================================================================
# LineageRunEvent.from_context — job identity and fields
# ============================================================================


def test_from_context_should_map_job_fields(job_context: Context):
    # Act
    result = LineageRunEvent.from_context(job_context, LineageRunEventType.START)

    # Assert
    actual = (
        result.job.namespace,
        result.job.name,
        result.job.job_type,
        result.job.processing_type,
        result.job.integration,
    )
    expected = (
        "acme.latam.ecommerce.checkout.raw",
        "test_job",
        "JobStub",
        "BATCH",
        "test_runner",
    )
    assert actual == expected


def test_from_context_should_use_executed_at_as_timestamp(job_context: Context):
    # Arrange
    executed_at = pendulum.datetime(2024, 6, 15, 12, 0, 0, tz="UTC")
    job_context.executed_at = executed_at

    # Act
    result = LineageRunEvent.from_context(job_context, LineageRunEventType.START)

    # Assert
    actual = result.timestamp
    expected = executed_at
    assert actual == expected


def test_from_context_should_fallback_timestamp_to_utcnow_when_executed_at_is_none(
    job_context: Context,
):
    # Arrange
    job_context.executed_at = None

    # Act
    result = LineageRunEvent.from_context(job_context, LineageRunEventType.START)

    # Assert
    assert isinstance(result.timestamp, pendulum.DateTime)


def test_from_context_should_map_run_identity_fields(job_context: Context):
    # Act
    result = LineageRunEvent.from_context(job_context, LineageRunEventType.START)

    # Assert
    actual = (
        result.run_id,
        result.producer,
    )
    expected = (
        job_context.run_id,
        config.app_identifier,
    )
    assert actual == expected


def test_from_context_should_map_governance_tags(job_context: Context):
    # Act
    result = LineageRunEvent.from_context(job_context, LineageRunEventType.START)

    # Assert
    actual = result.tags
    expected = {
        "org": "acme",
        "region": "latam",
        "domain": "ecommerce",
        "subdomain": "checkout",
        "layer": "raw",
        "product": "sales",
        "model": "orders",
        "owner": "platform",
        "maintainer": "data-team",
        "cost_center": "cc-123",
        "env": "test",
    }
    assert actual == expected


# ============================================================================
# LineageRunEvent.from_context — parent run
# ============================================================================


def test_from_context_should_unset_parent_when_job_context(job_context: Context):
    # Act
    result = LineageRunEvent.from_context(job_context, LineageRunEventType.START)

    # Assert
    actual = result.parent
    expected = None
    assert actual == expected


def test_from_context_should_set_parent_when_step_context(
    input_context: Context, job_context: Context
):
    # Act
    result = LineageRunEvent.from_context(input_context, LineageRunEventType.START)

    # Assert
    actual = (
        result.parent.run_id,
        result.parent.job_name,
        result.parent.namespace,
    )
    expected = (
        job_context.run_id,
        "test_job",
        "acme.latam.ecommerce.checkout.raw",
    )
    assert actual == expected


# ============================================================================
# LineageRunEvent.from_context — inputs and outputs
# ============================================================================


def test_from_context_should_map_inputs(job_context: Context):
    # Arrange
    inputs = ["sales.orders", "sales.customers"]

    # Act
    result = LineageRunEvent.from_context(job_context, LineageRunEventType.START, inputs)

    # Assert
    actual = [(d.namespace, d.name) for d in result.inputs]
    expected = [
        ("acme.latam.ecommerce.checkout.raw", "sales.orders"),
        ("acme.latam.ecommerce.checkout.raw", "sales.customers"),
    ]
    assert actual == expected


def test_from_context_should_map_outputs(job_context: Context):
    # Arrange
    outputs = ["sales.summary"]

    # Act
    result = LineageRunEvent.from_context(
        ctx=job_context,
        type=LineageRunEventType.COMPLETE,
        outputs=outputs,
    )

    # Assert
    actual = [(d.namespace, d.name) for d in result.outputs]
    expected = [
        ("acme.latam.ecommerce.checkout.raw", "sales.summary"),
    ]
    assert actual == expected


def test_from_context_should_default_datasets_to_empty(job_context: Context):
    # Act
    result = LineageRunEvent.from_context(job_context, LineageRunEventType.START)

    # Assert
    actual = (result.inputs, result.outputs)
    expected = ([], [])
    assert actual == expected


# ============================================================================
# LineageRunEvent.from_context — event type mapping
# ============================================================================


@pytest.mark.parametrize(
    "event_type,expected_value",
    [
        (LineageRunEventType.START, "START"),
        (LineageRunEventType.COMPLETE, "COMPLETE"),
        (LineageRunEventType.FAIL, "FAIL"),
        (LineageRunEventType.ABORT, "ABORT"),
    ],
)
def test_from_context_should_map_event_type(
    job_context: Context, event_type: LineageRunEventType, expected_value: str
):
    # Act
    result = LineageRunEvent.from_context(job_context, event_type)

    # Assert
    actual = result.type
    expected = expected_value
    assert actual == expected


# ============================================================================
# LineageRunEvent.from_context — streaming processing type
# ============================================================================


def test_from_context_should_use_streaming_when_runner_is_streaming(
    job_context: Context,
):
    # Arrange
    job_context.runner.streaming = True

    # Act
    result = LineageRunEvent.from_context(
        job_context,
        LineageRunEventType.START,
    )

    # Assert
    actual = result.job.processing_type
    expected = "STREAMING"
    assert actual == expected
