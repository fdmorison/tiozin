import pytest

from tests.stubs import LineageRegistryStub
from tiozin import Context, LineageDataset, LineageRunEvent

# ============================================================================
# LineageRegistry helpers — event type and identifier
# ============================================================================


@pytest.mark.parametrize(
    "method,expected_type",
    [
        ("start", LineageRunEvent.START),
        ("complete", LineageRunEvent.COMPLETE),
        ("fail", LineageRunEvent.FAIL),
        ("abort", LineageRunEvent.ABORT),
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
    actual = (
        lineage_registry_stub.captured_event.type,
        lineage_registry_stub.captured_identifier,
    )
    expected = (
        expected_type,
        job_context.run_id,
    )
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
        LineageDataset(namespace="s3://my-bucket", name="sales/orders"),
        LineageDataset(namespace="s3://my-bucket", name="sales/customers"),
    ]

    # Act
    lineage_registry_stub.start(inputs=inputs)

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
        LineageDataset(namespace="s3://my-bucket", name="sales/summary"),
    ]

    # Act
    lineage_registry_stub.start(outputs=outputs)

    # Assert
    actual = [(d.namespace, d.name) for d in lineage_registry_stub.captured_event.outputs]
    expected = [
        ("s3://my-bucket", "sales/summary"),
    ]
    assert actual == expected
