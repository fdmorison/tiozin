import pytest
from pydantic import ValidationError

from tiozin.api.metadata.transform_manifest import TransformManifest


def test_manifest_should_accept_minimum_transform():
    # Arrange
    data = {
        "kind": "TestTransform",
        "name": "test_transform",
    }

    # Act
    TransformManifest(**data)

    # Assert
    assert True


@pytest.mark.parametrize(
    "field_to_remove",
    ["kind", "name"],
)
def test_manifest_should_reject_transform_without_required_field(field_to_remove):
    # Arrange
    data = {
        "kind": "TestTransform",
        "name": "test_transform",
    }
    del data[field_to_remove]

    # Act
    with pytest.raises(ValidationError):
        TransformManifest(**data)


@pytest.mark.parametrize(
    "field_name,field_value",
    [
        ("description", "Test transform description"),
        ("org", "test_org"),
        ("region", "test_region"),
        ("domain", "test_domain"),
        ("subdomain", "test_subdomain"),
        ("layer", "test_layer"),
        ("product", "test_product"),
        ("model", "test_model"),
    ],
)
def test_manifest_should_accept_transform_with_optional_fields(field_name, field_value):
    # Arrange
    data = {
        "kind": "TestTransform",
        "name": "test_transform",
        field_name: field_value,
    }

    # Act
    manifest = TransformManifest(**data)

    # Assert
    actual = getattr(manifest, field_name)
    expected = field_value
    assert actual == expected


@pytest.mark.parametrize(
    "field_name,invalid_value",
    [
        ("kind", 123),
        ("name", 456),
        ("description", 789),
    ],
)
def test_manifest_should_reject_transform_with_invalid_field_types(field_name, invalid_value):
    # Arrange
    data = {
        "kind": "TestTransform",
        "name": "test_transform",
        field_name: invalid_value,
    }

    # Act
    with pytest.raises(ValidationError):
        TransformManifest(**data)


def test_manifest_should_have_correct_defaults():
    # Arrange
    data = {
        "kind": "TestTransform",
        "name": "test_transform",
    }

    # Act
    manifest = TransformManifest(**data)

    # Assert
    actual = manifest
    expected = TransformManifest(
        kind="TestTransform",
        name="test_transform",
        description=None,
        org=None,
        region=None,
        domain=None,
        subdomain=None,
        layer=None,
        product=None,
        model=None,
    )
    assert actual == expected
