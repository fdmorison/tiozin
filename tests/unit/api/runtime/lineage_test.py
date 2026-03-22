from tiozin.family.tio_kernel import NoOpInput, NoOpOutput, NoOpTransform

# ============================================================================
# Default lineage() fallback — Input, Output, Transform
# ============================================================================

_KWARGS = dict(
    name="test",
    org="acme",
    region="latam",
    domain="ecommerce",
    subdomain="checkout",
    layer="raw",
    product="sales",
    model="orders",
)


def test_input_should_return_logical_dataset_as_input_when_lineage_is_not_overridden():
    # Arrange
    step = NoOpInput(**_KWARGS)

    # Act
    result = step.lineage()

    # Assert
    actual = (
        result.inputs[0].namespace,
        result.inputs[0].name,
    )
    expected = (
        "acme.latam.ecommerce.checkout",
        "raw.sales.orders",
    )
    assert actual == expected


def test_output_should_return_logical_dataset_as_output_when_lineage_is_not_overridden():
    # Arrange
    step = NoOpOutput(**_KWARGS)

    # Act
    result = step.lineage()

    # Assert
    actual = (
        result.outputs[0].namespace,
        result.outputs[0].name,
    )
    expected = (
        "acme.latam.ecommerce.checkout",
        "raw.sales.orders",
    )
    assert actual == expected


def test_transform_should_return_logical_dataset_as_output_when_lineage_is_not_overridden():
    # Arrange
    step = NoOpTransform(**_KWARGS)

    # Act
    result = step.lineage()

    # Assert
    actual = (
        result.outputs[0].namespace,
        result.outputs[0].name,
    )
    expected = (
        "acme.latam.ecommerce.checkout",
        "raw.sales.orders",
    )
    assert actual == expected
