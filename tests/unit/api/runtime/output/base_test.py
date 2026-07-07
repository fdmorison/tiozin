from tests.stubs import OutputStub

# =============================================================================
# Testing Output.to_resource_dict
# =============================================================================


def test_output_should_expose_resource_fields(output_stub: OutputStub):
    # Act
    result = output_stub.to_resource_dict()

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
