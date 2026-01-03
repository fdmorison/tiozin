from copy import deepcopy

import pytest
from pydantic import ValidationError

from tiozin.api.metadata.transform_manifest import TransformManifest

compact_transform = {
    "kind": "TestTransform",
    "name": "test_transform",
}


def test_manifest_should_accept_minimum_transform():
    # Arrange
    data = compact_transform

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
    data = deepcopy(compact_transform)
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
        ("product", "test_product"),
        ("model", "test_model"),
        ("layer", "test_layer"),
    ],
)
def test_manifest_should_accept_transform_with_optional_fields(field_name, field_value):
    # Arrange
    data = deepcopy(compact_transform)
    data[field_name] = field_value

    # Act
    manifest = TransformManifest(**data)

    # Assert
    assert getattr(manifest, field_name) == field_value


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
    data = deepcopy(compact_transform)
    data[field_name] = invalid_value

    # Act
    with pytest.raises(ValidationError):
        TransformManifest(**data)


def test_manifest_should_have_correct_defaults():
    # Arrange
    data = compact_transform

    # Act
    manifest = TransformManifest(**data)

    # Assert
    assert manifest.description is None
    assert manifest.org is None
    assert manifest.region is None
    assert manifest.domain is None
    assert manifest.product is None
    assert manifest.model is None
    assert manifest.layer is None
