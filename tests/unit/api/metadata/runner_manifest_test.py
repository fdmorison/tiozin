from typing import Any

import pytest
from pydantic import ValidationError

from tiozin.api.metadata.runner_manifest import RunnerManifest


def test_manifest_should_accept_minimum_runner():
    # Arrange
    data = {
        "kind": "TestRunner",
    }

    # Act
    RunnerManifest(**data)

    # Assert
    assert True


def test_manifest_should_reject_runner_without_kind():
    # Arrange
    data = {}

    # Act
    with pytest.raises(ValidationError):
        RunnerManifest(**data)


@pytest.mark.parametrize(
    "field_name,field_value",
    [
        ("name", "test_runner"),
        ("description", "Test runner description"),
        ("streaming", True),
        ("streaming", False),
    ],
)
def test_manifest_should_accept_runner_with_optional_fields(field_name, field_value):
    # Arrange
    data = {
        "kind": "TestRunner",
        field_name: field_value,
    }

    # Act
    manifest = RunnerManifest(**data)

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
        ("streaming", "not_a_bool"),
    ],
)
def test_manifest_should_reject_runner_with_invalid_field_types(
    field_name: str, invalid_value: Any
):
    # Arrange
    data = {
        "kind": "TestRunner",
        field_name: invalid_value,
    }

    # Act
    with pytest.raises(ValidationError):
        RunnerManifest(**data)


def test_manifest_should_have_correct_defaults():
    # Arrange
    data = {
        "kind": "TestRunner",
    }

    # Act
    manifest = RunnerManifest(**data)

    # Assert
    actual = manifest
    expected = RunnerManifest(
        kind="TestRunner",
        name=None,
        description=None,
        streaming=False,
    )
    assert actual == expected
