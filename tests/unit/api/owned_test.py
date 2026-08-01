import pytest
from pydantic import BaseModel, ValidationError

from tiozin.api.owned import Owned


class Entity:
    def __init__(self, name: str = None) -> None:
        self.name = name


class OwnedResource(Owned):
    pass


class MixedOwnedResource(Owned, Entity):
    pass


class OwnedPydanticResource(Owned, BaseModel):
    pass


# ============================================================================
# Testing Owned.__init__
# ============================================================================


def test_owned_mixin_should_assign_ownership_fields():
    # Act
    resource = OwnedResource(
        owner="analytics",
        maintainer="data-platform",
        cost_center="CC-1234",
        labels={"tier": "gold"},
    )

    # Assert
    actual = (
        resource.owner,
        resource.maintainer,
        resource.cost_center,
        resource.labels,
    )
    expected = (
        "analytics",
        "data-platform",
        "CC-1234",
        {"tier": "gold"},
    )
    assert actual == expected


def test_owned_mixin_should_default_ownership_fields():
    # Act
    resource = OwnedResource()

    # Assert
    actual = (
        resource.owner,
        resource.maintainer,
        resource.cost_center,
        resource.labels,
    )
    expected = (None, None, None, {})
    assert actual == expected


def test_owned_mixin_should_default_labels_to_empty_dict_when_labels_is_none():
    # Act
    resource = OwnedResource(labels=None)

    # Assert
    actual = resource.labels
    expected = {}
    assert actual == expected


def test_owned_mixin_should_forward_non_ownership_options_to_next_class():
    # Act
    resource = MixedOwnedResource(owner="analytics", name="orders")

    # Assert
    actual = (resource.owner, resource.name)
    expected = ("analytics", "orders")
    assert actual == expected


# ============================================================================
# Testing Owned as a pydantic model
# ============================================================================


def test_owned_model_should_assign_ownership_fields():
    # Act
    resource = OwnedPydanticResource(
        owner="analytics",
        maintainer="data-platform",
        cost_center="CC-1234",
        labels={"tier": "gold"},
    )

    # Assert
    actual = resource.model_dump()
    expected = {
        "owner": "analytics",
        "maintainer": "data-platform",
        "cost_center": "CC-1234",
        "labels": {"tier": "gold"},
    }
    assert actual == expected


def test_owned_model_should_default_ownership_fields():
    # Act
    resource = OwnedPydanticResource()

    # Assert
    actual = resource.model_dump()
    expected = {
        "owner": None,
        "maintainer": None,
        "cost_center": None,
        "labels": {},
    }
    assert actual == expected


@pytest.mark.parametrize("field", ["owner", "maintainer", "cost_center"])
def test_owned_model_should_accept_none_for_scalar_fields(field):
    # Act
    result = OwnedPydanticResource(**{field: None})

    # Assert
    assert getattr(result, field) is None


def test_owned_model_should_describe_ownership_fields():
    # Act
    result = OwnedPydanticResource.model_fields

    # Assert
    actual = sorted(name for name, field in result.items() if field.description)
    expected = ["cost_center", "labels", "maintainer", "owner"]
    assert actual == expected


@pytest.mark.parametrize("labels", ["gold", None])
def test_owned_model_should_raise_validation_error_when_labels_is_not_a_dict(labels):
    # Act
    with pytest.raises(ValidationError) as error:
        OwnedPydanticResource(labels=labels)

    # Assert
    actual = [(item["loc"][0], item["type"]) for item in error.value.errors()]
    expected = [("labels", "dict_type")]
    assert actual == expected


# ============================================================================
# Testing Owned's frozen ownership fields
# ============================================================================


@pytest.mark.parametrize(
    "field, value",
    [
        ("owner", "marketing"),
        ("maintainer", "data-engineering"),
        ("cost_center", "CC-9999"),
        ("labels", {"tier": "silver"}),
    ],
)
def test_owned_model_should_raise_validation_error_when_ownership_field_is_reassigned(field, value):
    # Arrange
    resource = OwnedPydanticResource(
        owner="analytics",
        maintainer="data-platform",
        cost_center="CC-1234",
        labels={"tier": "gold"},
    )

    # Act
    with pytest.raises(ValidationError) as error:
        setattr(resource, field, value)

    # Assert
    actual = [item["type"] for item in error.value.errors()]
    expected = ["frozen_field"]
    assert actual == expected


def test_owned_model_should_update_labels_content():
    # Arrange
    resource = OwnedPydanticResource(labels={"tier": "gold"})

    # Act
    resource.labels["squad"] = "checkout"

    # Assert
    actual = resource.labels
    expected = {"tier": "gold", "squad": "checkout"}
    assert actual == expected


# ============================================================================
# Testing Owned.to_owned_dict
# ============================================================================


def test_to_owned_dict_should_return_ownership_fields():
    # Arrange
    resource = OwnedResource(
        owner="analytics",
        maintainer="data-platform",
        cost_center="CC-1234",
        labels={"tier": "gold"},
    )

    # Act
    result = resource.to_owned_dict()

    # Assert
    actual = result
    expected = {
        "owner": "analytics",
        "maintainer": "data-platform",
        "cost_center": "CC-1234",
        "labels": {"tier": "gold"},
    }
    assert actual == expected


def test_to_owned_dict_should_return_none_for_unset_fields():
    # Arrange
    resource = OwnedResource()

    # Act
    result = resource.to_owned_dict()

    # Assert
    actual = result
    expected = {
        "owner": None,
        "maintainer": None,
        "cost_center": None,
        "labels": {},
    }
    assert actual == expected


def test_to_owned_dict_should_nest_labels_when_flat_is_none():
    # Arrange
    resource = OwnedResource(
        owner="analytics",
        maintainer="data-platform",
        cost_center="CC-1234",
        labels={"tier": "gold"},
    )

    # Act
    result = resource.to_owned_dict(flat=None)

    # Assert
    actual = result
    expected = {
        "owner": "analytics",
        "maintainer": "data-platform",
        "cost_center": "CC-1234",
        "labels": {"tier": "gold"},
    }
    assert actual == expected


# ============================================================================
# Testing Owned.to_owned_dict with flattened labels
# ============================================================================


def test_to_owned_dict_should_flatten_labels_when_flat():
    # Arrange
    resource = OwnedResource(
        owner="analytics",
        maintainer="data-platform",
        cost_center="CC-1234",
        labels={"tier": "gold", "squad": "checkout"},
    )

    # Act
    result = resource.to_owned_dict(flat=True)

    # Assert
    actual = result
    expected = {
        "owner": "analytics",
        "maintainer": "data-platform",
        "cost_center": "CC-1234",
        "tier": "gold",
        "squad": "checkout",
    }
    assert actual == expected


def test_to_owned_dict_should_return_none_for_unset_fields_when_flat():
    # Arrange
    resource = OwnedResource()

    # Act
    result = resource.to_owned_dict(flat=True)

    # Assert
    actual = result
    expected = {
        "owner": None,
        "maintainer": None,
        "cost_center": None,
    }
    assert actual == expected


def test_to_owned_dict_should_prefer_label_over_field_when_flat():
    # Arrange
    resource = OwnedResource(
        owner="analytics",
        labels={"owner": "marketing"},
    )

    # Act
    result = resource.to_owned_dict(flat=True)

    # Assert
    actual = result
    expected = {
        "owner": "marketing",
        "maintainer": None,
        "cost_center": None,
    }
    assert actual == expected
