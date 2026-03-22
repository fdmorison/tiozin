import pytest

from tests.stubs import LineageRegistryStub
from tiozin.api.metadata.lineage.model import LineageRunEventType
from tiozin.api.runtime.context import Context

# ============================================================================
# LineageRegistry helpers — event type and identifier
# ============================================================================


@pytest.mark.parametrize(
    "method,expected_type",
    [
        ("start", LineageRunEventType.START),
        ("complete", LineageRunEventType.COMPLETE),
        ("fail", LineageRunEventType.FAIL),
        ("abort", LineageRunEventType.ABORT),
    ],
)
def test_helper_should_emit_event_with_correct_type(
    lineage_registry_stub: LineageRegistryStub,
    job_context: Context,
    method: str,
    expected_type: LineageRunEventType,
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
    inputs = ["sales.orders", "sales.customers"]

    # Act
    lineage_registry_stub.start(inputs=inputs)

    # Assert
    actual = [d.name for d in lineage_registry_stub.captured_event.inputs]
    expected = ["sales.orders", "sales.customers"]
    assert actual == expected


@pytest.mark.usefixtures("job_context")
def test_start_should_forward_outputs(
    lineage_registry_stub: LineageRegistryStub,
):
    # Arrange
    outputs = ["sales.summary"]

    # Act
    lineage_registry_stub.start(outputs=outputs)

    # Assert
    actual = [d.name for d in lineage_registry_stub.captured_event.outputs]
    expected = ["sales.summary"]
    assert actual == expected
