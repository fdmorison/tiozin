import pytest
from pydantic import ValidationError

from tiozin.api import Input
from tiozin.api.metadata.input_manifest import InputManifest


def test_manifest_for_kind_should_return_input_type():
    # Act
    actual = InputManifest.for_kind()

    # Assert
    expected = Input
    assert actual == expected


def test_manifest_should_accept_minimum_input():
    # Arrange
    data = {
        "kind": "TestInput",
        "name": "test_input",
    }

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
    data = {
        "kind": "TestInput",
        "name": "test_input",
    }
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
        ("subdomain", "test_subdomain"),
        ("layer", "test_layer"),
        ("product", "test_product"),
        ("model", "test_model"),
        ("schema", "test_schema"),
        ("schema_subject", "test_subject"),
        ("schema_version", "1.0.0"),
    ],
)
def test_manifest_should_accept_input_with_optional_fields(field_name, field_value):
    # Arrange
    data = {
        "kind": "TestInput",
        "name": "test_input",
    }
    data[field_name] = field_value

    # Act
    manifest = InputManifest(**data)

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
def test_manifest_should_reject_input_with_invalid_field_types(field_name, invalid_value):
    # Arrange
    data = {
        "kind": "TestInput",
        "name": "test_input",
        field_name: invalid_value,
    }

    # Act
    with pytest.raises(ValidationError):
        InputManifest(**data)


def test_manifest_should_have_correct_defaults():
    # Arrange
    data = {
        "kind": "TestInput",
        "name": "test_input",
    }

    # Act
    manifest = InputManifest(**data)

    # Assert
    actual = manifest
    expected = InputManifest(
        kind="TestInput",
        name="test_input",
        description=None,
        org=None,
        region=None,
        domain=None,
        subdomain=None,
        layer=None,
        product=None,
        model=None,
        schema=None,
        schema_subject=None,
        schema_version=None,
    )
    assert actual == expected
