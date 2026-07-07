from tests.stubs import TransformStub

# =============================================================================
# Testing Transform.to_resource_dict
# =============================================================================


def test_transform_should_expose_resource_fields(transform_stub: TransformStub):
    # Act
    result = transform_stub.to_resource_dict()

    # Assert
    actual = result
    expected = {
        "org": "acme",
        "region": "latam",
        "domain": "ecommerce",
        "subdomain": "checkout",
        "layer": "raw",
        "product": "sales",
        "model": "orders",
    }
    assert actual == expected
