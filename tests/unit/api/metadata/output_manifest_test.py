import pytest
from pydantic import ValidationError

from tiozin.api import Output
from tiozin.api.metadata.output_manifest import OutputManifest


def test_manifest_for_kind_should_return_output_type():
    # Act
    actual = OutputManifest.for_kind()

    # Assert
    expected = Output
    assert actual == expected


def test_manifest_should_accept_minimum_output():
    # Arrange
    data = {
        "kind": "TestOutput",
        "name": "test_output",
    }

    # Act
    OutputManifest(**data)

    # Assert
    assert True


@pytest.mark.parametrize(
    "field_to_remove",
    ["kind", "name"],
)
def test_manifest_should_reject_output_without_required_field(field_to_remove):
    # Arrange
    data = {
        "kind": "TestOutput",
        "name": "test_output",
    }
    del data[field_to_remove]

    # Act
    with pytest.raises(ValidationError):
        OutputManifest(**data)


@pytest.mark.parametrize(
    "field_name,field_value",
    [
        ("description", "Test output description"),
        ("org", "test_org"),
        ("region", "test_region"),
        ("domain", "test_domain"),
        ("subdomain", "test_subdomain"),
        ("layer", "test_layer"),
        ("product", "test_product"),
        ("model", "test_model"),
    ],
)
def test_manifest_should_accept_output_with_optional_fields(field_name, field_value):
    # Arrange
    data = {
        "kind": "TestOutput",
        "name": "test_output",
        field_name: field_value,
    }

    # Act
    manifest = OutputManifest(**data)

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
def test_manifest_should_reject_output_with_invalid_field_types(field_name, invalid_value):
    # Arrange
    data = {
        "kind": "TestOutput",
        "name": "test_output",
        field_name: invalid_value,
    }

    # Act
    with pytest.raises(ValidationError):
        OutputManifest(**data)


def test_manifest_should_have_correct_defaults():
    # Arrange
    data = {
        "kind": "TestOutput",
        "name": "test_output",
    }

    # Act
    manifest = OutputManifest(**data)

    # Assert
    actual = manifest
    expected = OutputManifest(
        kind="TestOutput",
        name="test_output",
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
