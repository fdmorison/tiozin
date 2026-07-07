from tests.stubs import InputStub

# =============================================================================
# Testing Input.to_resource_dict
# =============================================================================


def test_input_should_expose_resource_fields(input_stub: InputStub):
    # Act
    result = input_stub.to_resource_dict()

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
