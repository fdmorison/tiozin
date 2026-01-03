from copy import deepcopy

import pytest
from pydantic import ValidationError

from tiozin.api.metadata.input_manifest import InputManifest

compact_input = {
    "kind": "TestInput",
    "name": "test_input",
}


def test_manifest_should_accept_minimum_input():
    # Arrange
    data = compact_input

    # Act
    InputManifest(**data)

    # Assert
    assert True


@pytest.mark.parametrize(
    "field_to_remove",
    ["kind", "name"],
)
def test_manifest_should_reject_input_without_required_field(field_to_remove):
    # Arrange
    data = deepcopy(compact_input)
    del data[field_to_remove]

    # Act
    with pytest.raises(ValidationError):
        InputManifest(**data)


@pytest.mark.parametrize(
    "field_name,field_value",
    [
        ("description", "Test input description"),
        ("org", "test_org"),
        ("region", "test_region"),
        ("domain", "test_domain"),
        ("product", "test_product"),
        ("model", "test_model"),
        ("layer", "test_layer"),
        ("schema", "test_schema"),
        ("schema_subject", "test_subject"),
        ("schema_version", "1.0.0"),
    ],
)
def test_manifest_should_accept_input_with_optional_fields(field_name, field_value):
    # Arrange
    data = deepcopy(compact_input)
    data[field_name] = field_value

    # Act
    manifest = InputManifest(**data)

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
def test_manifest_should_reject_input_with_invalid_field_types(field_name, invalid_value):
    # Arrange
    data = deepcopy(compact_input)
    data[field_name] = invalid_value

    # Act
    with pytest.raises(ValidationError):
        InputManifest(**data)


def test_manifest_should_have_correct_defaults():
    # Arrange
    data = compact_input

    # Act
    manifest = InputManifest(**data)

    # Assert
    assert manifest.description is None
    assert manifest.org is None
    assert manifest.region is None
    assert manifest.domain is None
    assert manifest.product is None
    assert manifest.model is None
    assert manifest.layer is None
    assert manifest.schema is None
    assert manifest.schema_subject is None
    assert manifest.schema_version is None
