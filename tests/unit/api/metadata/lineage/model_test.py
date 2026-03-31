import pendulum
import pytest

from tests import config
from tiozin import Dataset, LineageRunEvent
from tiozin.api.context import Context

# ============================================================================
# LineageRunEvent.from_context — job identity and fields
# ============================================================================


def test_from_context_should_map_job_fields(job_context: Context):
    # Act
    result = LineageRunEvent.from_context(job_context, LineageRunEvent.START)

    # Assert
    actual = (
        result.job.namespace,
        result.job.name,
        result.job.type,
        result.job.processing_type,
        result.job.integration,
    )
    expected = (
        "acme.latam.ecommerce.checkout",
        "test_job",
        "JOB",
        "BATCH",
        "TIOZIN",
    )
    assert actual == expected


def test_from_context_should_use_executed_at_as_timestamp(job_context: Context):
    # Arrange
    executed_at = pendulum.datetime(2024, 6, 15, 12, 0, 0, tz="UTC")
    job_context.executed_at = executed_at

    # Act
    result = LineageRunEvent.from_context(job_context, LineageRunEvent.START)

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
    result = LineageRunEvent.from_context(job_context, LineageRunEvent.START)

    # Assert
    assert isinstance(result.timestamp, pendulum.DateTime)


def test_from_context_should_map_run_identity_fields(job_context: Context):
    # Act
    result = LineageRunEvent.from_context(job_context, LineageRunEvent.START)

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
    result = LineageRunEvent.from_context(job_context, LineageRunEvent.START)

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
    result = LineageRunEvent.from_context(job_context, LineageRunEvent.START)

    # Assert
    actual = result.parent
    expected = None
    assert actual == expected


def test_from_context_should_use_qualified_slug_as_job_name_when_step_context(
    input_context: Context,
):
    # Act
    result = LineageRunEvent.from_context(input_context, LineageRunEvent.START)

    # Assert
    actual = (
        result.job.namespace,
        result.job.name,
    )
    expected = (
        input_context.namespace,
        input_context.qualified_slug,
    )
    assert actual == expected


def test_from_context_should_set_parent_when_step_context(
    input_context: Context, job_context: Context
):
    # Act
    result = LineageRunEvent.from_context(input_context, LineageRunEvent.START)

    # Assert
    actual = (
        result.parent.run_id,
        result.parent.name,
        result.parent.namespace,
    )
    expected = (
        job_context.run_id,
        "test_job",
        "acme.latam.ecommerce.checkout",
    )
    assert actual == expected


# ============================================================================
# LineageRunEvent.from_context — inputs and outputs
# ============================================================================


def test_from_context_should_map_inputs(job_context: Context):
    # Arrange
    inputs = [
        Dataset(data=[], namespace="s3://my-bucket", name="sales/orders"),
        Dataset(data=[], namespace="s3://my-bucket", name="sales/customers"),
    ]

    # Act
    result = LineageRunEvent.from_context(job_context, LineageRunEvent.START, inputs)

    # Assert
    actual = [(d.namespace, d.name) for d in result.inputs]
    expected = [
        ("s3://my-bucket", "sales/orders"),
        ("s3://my-bucket", "sales/customers"),
    ]
    assert actual == expected


def test_from_context_should_map_outputs(job_context: Context):
    # Arrange
    outputs = [
        Dataset(data=[], namespace="s3://my-bucket", name="sales/summary"),
    ]

    # Act
    result = LineageRunEvent.from_context(
        ctx=job_context,
        type=LineageRunEvent.COMPLETE,
        outputs=outputs,
    )

    # Assert
    actual = [(d.namespace, d.name) for d in result.outputs]
    expected = [
        ("s3://my-bucket", "sales/summary"),
    ]
    assert actual == expected


def test_from_context_should_default_datasets_to_empty(job_context: Context):
    # Act
    result = LineageRunEvent.from_context(job_context, LineageRunEvent.START)

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
        (LineageRunEvent.START, "START"),
        (LineageRunEvent.COMPLETE, "COMPLETE"),
        (LineageRunEvent.FAIL, "FAIL"),
        (LineageRunEvent.ABORT, "ABORT"),
    ],
)
def test_from_context_should_map_event_type(
    job_context: Context, event_type: str, expected_value: str
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
        LineageRunEvent.START,
    )

    # Assert
    actual = result.job.processing_type
    expected = "STREAMING"
    assert actual == expected
