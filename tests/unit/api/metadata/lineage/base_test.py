import pytest

from tests.stubs import LineageRegistryStub
from tiozin import Context, Dataset, LineageRunEvent

# ============================================================================
# LineageRegistry helpers — event type and identifier
# ============================================================================


@pytest.mark.parametrize(
    "method,expected_type",
    [
        ("run_started", LineageRunEvent.START),
        ("run_completed", LineageRunEvent.COMPLETE),
        ("run_failed", LineageRunEvent.FAIL),
        ("run_aborted", LineageRunEvent.ABORT),
    ],
)
def test_helper_should_emit_event_with_correct_type(
    lineage_registry_stub: LineageRegistryStub,
    job_context: Context,
    method: str,
    expected_type: str,
):
    # Act
    getattr(lineage_registry_stub, method)()

    # Assert
    actual = lineage_registry_stub.captured_event.type
    expected = expected_type
    assert actual == expected


# ============================================================================
# LineageRegistry helpers — datasets pass-through
# ============================================================================


@pytest.mark.usefixtures("job_context")
def test_start_should_forward_inputs(
    lineage_registry_stub: LineageRegistryStub,
):
    # Arrange
    inputs = [
        Dataset(data=[], namespace="s3://my-bucket", name="sales/orders"),
        Dataset(data=[], namespace="s3://my-bucket", name="sales/customers"),
    ]

    # Act
    lineage_registry_stub.run_started(inputs=inputs)

    # Assert
    actual = [(d.namespace, d.name) for d in lineage_registry_stub.captured_event.inputs]
    expected = [
        ("s3://my-bucket", "sales/orders"),
        ("s3://my-bucket", "sales/customers"),
    ]
    assert actual == expected


@pytest.mark.usefixtures("job_context")
def test_start_should_forward_outputs(
    lineage_registry_stub: LineageRegistryStub,
):
    # Arrange
    outputs = [
        Dataset(data=[], namespace="s3://my-bucket", name="sales/summary"),
    ]

    # Act
    lineage_registry_stub.run_started(outputs=outputs)

    # Assert
    actual = [(d.namespace, d.name) for d in lineage_registry_stub.captured_event.outputs]
    expected = [
        ("s3://my-bucket", "sales/summary"),
    ]
    assert actual == expected
