import pytest
from pydantic import BaseModel, ValidationError

from tiozin.api.resourceful import OptionalResourceful, Resourceful
from tiozin.exceptions import RequiredArgumentError


class Entity:
    def __init__(self, name: str = None) -> None:
        self.name = name


class OptionalResource(OptionalResourceful):
    pass


class RequiredResource(Resourceful):
    pass


class MixedOptionalResource(OptionalResourceful, Entity):
    pass


class MixedRequiredResource(Resourceful, Entity):
    pass


class OptionalPydanticResource(OptionalResourceful, BaseModel):
    pass


class RequiredPydanticResource(Resourceful, BaseModel):
    pass


# ============================================================================
# Testing Resourceful.__init__
# ============================================================================


def test_resource_mixin_should_assign_resource_fields():
    # Act
    resource = OptionalResource(
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
    resource = OptionalResource()

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


def test_resource_mixin_should_forward_non_resource_options_to_next_class():
    # Act
    resource = MixedOptionalResource(org="acme", name="orders")

    # Assert
    actual = (resource.org, resource.name)
    expected = ("acme", "orders")
    assert actual == expected


# ============================================================================
# Testing Resourceful as a pydantic model
# ============================================================================


def test_resource_model_should_assign_resource_fields():
    # Act
    resource = OptionalPydanticResource(
        org="acme",
        region="latam",
        domain="ecommerce",
        subdomain="checkout",
        layer="raw",
        product="sales",
        model="orders",
    )

    # Assert
    actual = resource.model_dump()
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


def test_resource_model_should_reassign_resource_field():
    # Arrange
    resource = OptionalPydanticResource(
        org="acme",
        region="latam",
        domain="ecommerce",
        subdomain="checkout",
        layer="raw",
        product="sales",
        model="orders",
    )

    # Act
    resource.org = "globex"

    # Assert
    actual = resource.org
    expected = "globex"
    assert actual == expected


def test_resource_model_should_default_resource_fields_to_none():
    # Act
    resource = OptionalPydanticResource()

    # Assert
    actual = resource.model_dump()
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


def test_resource_model_should_describe_resource_fields():
    # Act
    result = OptionalPydanticResource.model_fields

    # Assert
    actual = sorted(name for name, field in result.items() if field.description)
    expected = [
        "domain",
        "layer",
        "model",
        "org",
        "product",
        "region",
        "subdomain",
    ]
    assert actual == expected


# ============================================================================
# Testing Resourceful's required and frozen resource identity
# ============================================================================


def test_resource_mixin_should_raise_required_argument_when_no_resource_field_is_provided():
    # Act
    with pytest.raises(RequiredArgumentError) as error:
        RequiredResource()

    # Assert
    actual = str(error.value)
    expected = (
        "Missing required fields: "
        "'org', 'region', 'domain', 'subdomain', 'layer', 'product', 'model'"
    )
    assert actual == expected


@pytest.mark.parametrize("subdomain", [None, ""])
def test_resource_mixin_should_raise_required_argument_when_resource_field_is_empty(subdomain):
    # Act
    with pytest.raises(RequiredArgumentError) as error:
        RequiredResource(
            org="acme",
            region="latam",
            domain="ecommerce",
            subdomain=subdomain,
            layer="raw",
            product="sales",
            model="orders",
        )

    # Assert
    actual = str(error.value)
    expected = "Missing required fields: 'subdomain'"
    assert actual == expected


def test_resource_mixin_should_raise_required_argument_when_mixed_into_another_class():
    # Act
    with pytest.raises(RequiredArgumentError) as error:
        MixedRequiredResource(name="orders")

    # Assert
    actual = str(error.value)
    expected = (
        "Missing required fields: "
        "'org', 'region', 'domain', 'subdomain', 'layer', 'product', 'model'"
    )
    assert actual == expected


# Job relies on the plain-class path, so its resource identity stays reassignable.
def test_resource_mixin_should_reassign_resource_field():
    # Arrange
    resource = RequiredResource(
        org="acme",
        region="latam",
        domain="ecommerce",
        subdomain="checkout",
        layer="raw",
        product="sales",
        model="orders",
    )

    # Act
    resource.org = "globex"

    # Assert
    actual = resource.org
    expected = "globex"
    assert actual == expected


def test_resource_model_should_raise_validation_error_when_resource_field_is_missing():
    # Act
    with pytest.raises(ValidationError) as error:
        RequiredPydanticResource(org="acme")

    # Assert
    actual = sorted((item["loc"][0], item["type"]) for item in error.value.errors())
    expected = [
        ("domain", "missing"),
        ("layer", "missing"),
        ("model", "missing"),
        ("product", "missing"),
        ("region", "missing"),
        ("subdomain", "missing"),
    ]
    assert actual == expected


def test_resource_model_should_raise_validation_error_when_resource_field_is_empty():
    # Act
    with pytest.raises(ValidationError) as error:
        RequiredPydanticResource(
            org="acme",
            region="latam",
            domain="ecommerce",
            subdomain="",
            layer="raw",
            product="sales",
            model="orders",
        )

    # Assert
    actual = [(item["loc"][0], item["type"]) for item in error.value.errors()]
    expected = [("subdomain", "string_too_short")]
    assert actual == expected


def test_resource_model_should_raise_validation_error_when_validated_from_dict():
    # Act
    with pytest.raises(ValidationError) as error:
        RequiredPydanticResource.model_validate(
            {
                "org": "acme",
                "region": "latam",
                "domain": "ecommerce",
                "subdomain": "checkout",
                "layer": "raw",
                "product": "sales",
                "model": "",
            }
        )

    # Assert
    actual = [(item["loc"][0], item["type"]) for item in error.value.errors()]
    expected = [("model", "string_too_short")]
    assert actual == expected


@pytest.mark.parametrize(
    "field, value",
    [
        ("org", "globex"),
        ("region", "emea"),
        ("domain", "marketing"),
        ("subdomain", "campaigns"),
        ("layer", "silver"),
        ("product", "leads"),
        ("model", "contacts"),
    ],
)
def test_resource_model_should_raise_validation_error_when_resource_field_is_reassigned(
    field,
    value,
):
    # Arrange
    resource = RequiredPydanticResource(
        org="acme",
        region="latam",
        domain="ecommerce",
        subdomain="checkout",
        layer="raw",
        product="sales",
        model="orders",
    )

    # Act
    with pytest.raises(ValidationError) as error:
        setattr(resource, field, value)

    # Assert
    actual = [item["type"] for item in error.value.errors()]
    expected = ["frozen_field"]
    assert actual == expected


# ============================================================================
# Testing Resourceful.to_resource_dict
# ============================================================================


def test_resource_should_return_resource_fields():
    # Arrange
    resource = OptionalResource(
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
    resource = OptionalResource()

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
    resource = OptionalResource(
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


def test_qualified_domain_should_omit_unset_fields():
    # Arrange
    resource = OptionalResource(
        org="acme",
        domain="ecommerce",
    )

    # Act
    result = resource.qualified_domain

    # Assert
    actual = result
    expected = "acme.ecommerce"
    assert actual == expected


# ============================================================================
# Testing Resourceful.qualified_subdomain
# ============================================================================


def test_qualified_subdomain_should_return_dot_joined_subdomain_key():
    # Arrange
    resource = OptionalResource(
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


def test_qualified_subdomain_should_omit_unset_fields():
    # Arrange
    resource = OptionalResource(
        org="acme",
        domain="ecommerce",
        subdomain="checkout",
    )

    # Act
    result = resource.qualified_subdomain

    # Assert
    actual = result
    expected = "acme.ecommerce.checkout"
    assert actual == expected


# ============================================================================
# Testing Resourceful.qualified_product
# ============================================================================


def test_qualified_product_should_return_dot_joined_product_key():
    # Arrange
    resource = OptionalResource(
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


def test_qualified_product_should_omit_unset_fields():
    # Arrange
    resource = OptionalResource(
        layer="raw",
        model="orders",
    )

    # Act
    result = resource.qualified_product

    # Assert
    actual = result
    expected = "raw.orders"
    assert actual == expected


# ============================================================================
# Testing Resourceful.qualified_resource
# ============================================================================


def test_qualified_resource_should_return_dot_joined_resource_key():
    # Arrange
    resource = OptionalResource(
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


def test_qualified_resource_should_omit_unset_fields():
    # Arrange
    resource = OptionalResource(
        org="acme",
        domain="ecommerce",
        subdomain="checkout",
        layer="raw",
        product="sales",
    )

    # Act
    result = resource.qualified_resource

    # Assert
    actual = result
    expected = "acme.ecommerce.checkout.raw.sales"
    assert actual == expected


def test_qualified_resource_should_return_empty_when_no_field_is_set():
    # Arrange
    resource = OptionalResource()

    # Act
    result = resource.qualified_resource

    # Assert
    actual = result
    expected = ""
    assert actual == expected
