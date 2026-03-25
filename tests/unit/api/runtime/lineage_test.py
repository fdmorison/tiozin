from tiozin import Context
from tiozin.family.tio_kernel import NoOpInput, NoOpOutput, NoOpTransform

# ============================================================================
# Default lineage_datasets() fallback — Input, Output, Transform
# ============================================================================

_KWARGS = dict(
    org="acme",
    region="latam",
    domain="ecommerce",
    subdomain="checkout",
    layer="raw",
    product="sales",
    model="orders",
)


def test_input_should_return_logical_dataset_as_input_when_lineage_is_not_overridden(
    job_context: Context,
):
    # Arrange
    step = NoOpInput(name="test_input", **_KWARGS)

    # Act
    result = step.lineage_datasets()

    # Assert
    actual = (
        result.inputs[0].namespace,
        result.inputs[0].name,
    )
    expected = (
        job_context.namespace,
        f"{job_context.slug}.{step.slug}",
    )
    assert actual == expected


def test_output_should_return_logical_dataset_as_output_when_lineage_is_not_overridden(
    job_context: Context,
):
    # Arrange
    step = NoOpOutput(name="test_output", **_KWARGS)

    # Act
    result = step.lineage_datasets()

    # Assert
    actual = (
        result.outputs[0].namespace,
        result.outputs[0].name,
    )
    expected = (
        job_context.namespace,
        f"{job_context.slug}.{step.slug}",
    )
    assert actual == expected


def test_transform_should_return_logical_dataset_as_output_when_lineage_is_not_overridden(
    job_context: Context,
):
    # Arrange
    step = NoOpTransform(name="test_transform", **_KWARGS)

    # Act
    result = step.lineage_datasets()

    # Assert
    actual = (
        result.outputs[0].namespace,
        result.outputs[0].name,
    )
    expected = (
        job_context.namespace,
        f"{job_context.slug}.{step.slug}",
    )
    assert actual == expected
