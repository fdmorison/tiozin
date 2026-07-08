from tiozin.api.resourceful import Resourceful


class ResourceDummy(Resourceful):
    pass


# ============================================================================
# Testing Resourceful.__init__
# ============================================================================


def test_resource_mixin_should_assign_resource_fields():
    # Act
    resource = ResourceDummy(
        org="acme",
        region="latam",
        domain="ecommerce",
        subdomain="checkout",
        layer="raw",
        product="sales",
        model="orders",
    )

    # Assert
    actual = (
        resource.org,
        resource.region,
        resource.domain,
        resource.subdomain,
        resource.layer,
        resource.product,
        resource.model,
    )
    expected = (
        "acme",
        "latam",
        "ecommerce",
        "checkout",
        "raw",
        "sales",
        "orders",
    )
    assert actual == expected


def test_resource_mixin_should_default_resource_fields_to_none():
    # Act
    resource = ResourceDummy()

    # Assert
    actual = (
        resource.org,
        resource.region,
        resource.domain,
        resource.subdomain,
        resource.layer,
        resource.product,
        resource.model,
    )
    expected = (None, None, None, None, None, None, None)
    assert actual == expected


# ============================================================================
# Testing Resourceful.to_resource_dict
# ============================================================================


def test_resource_should_return_resource_fields():
    # Arrange
    resource = ResourceDummy(
        org="acme",
        region="latam",
        domain="ecommerce",
        subdomain="checkout",
        layer="raw",
        product="sales",
        model="orders",
    )

    # Act
    result = resource.to_resource_dict()

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


def test_resource_should_return_none_for_unset_fields():
    # Arrange
    resource = ResourceDummy()

    # Act
    result = resource.to_resource_dict()

    # Assert
    actual = result
    expected = {
        "org": None,
        "region": None,
        "domain": None,
        "subdomain": None,
        "layer": None,
        "product": None,
        "model": None,
    }
    assert actual == expected


# ============================================================================
# Testing Resourceful.qualified_domain
# ============================================================================


def test_qualified_domain_should_return_dot_joined_domain_key():
    # Arrange
    resource = ResourceDummy(
        org="acme",
        region="latam",
        domain="ecommerce",
        subdomain="checkout",
        layer="raw",
        product="sales",
        model="orders",
    )

    # Act
    result = resource.qualified_domain

    # Assert
    actual = result
    expected = "acme.latam.ecommerce"
    assert actual == expected


# ============================================================================
# Testing Resourceful.qualified_subdomain
# ============================================================================


def test_qualified_subdomain_should_return_dot_joined_subdomain_key():
    # Arrange
    resource = ResourceDummy(
        org="acme",
        region="latam",
        domain="ecommerce",
        subdomain="checkout",
        layer="raw",
        product="sales",
        model="orders",
    )

    # Act
    result = resource.qualified_subdomain

    # Assert
    actual = result
    expected = "acme.latam.ecommerce.checkout"
    assert actual == expected


# ============================================================================
# Testing Resourceful.qualified_product
# ============================================================================


def test_qualified_product_should_return_dot_joined_product_key():
    # Arrange
    resource = ResourceDummy(
        org="acme",
        region="latam",
        domain="ecommerce",
        subdomain="checkout",
        layer="raw",
        product="sales",
        model="orders",
    )

    # Act
    result = resource.qualified_product

    # Assert
    actual = result
    expected = "raw.sales.orders"
    assert actual == expected


# ============================================================================
# Testing Resourceful.qualified_resource
# ============================================================================


def test_qualified_resource_should_return_dot_joined_resource_key():
    # Arrange
    resource = ResourceDummy(
        org="acme",
        region="latam",
        domain="ecommerce",
        subdomain="checkout",
        layer="raw",
        product="sales",
        model="orders",
    )

    # Act
    result = resource.qualified_resource

    # Assert
    actual = result
    expected = "acme.latam.ecommerce.checkout.raw.sales.orders"
    assert actual == expected
