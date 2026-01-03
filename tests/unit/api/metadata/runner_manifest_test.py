from copy import deepcopy

import pytest
from pydantic import ValidationError

from tiozin.api.metadata.runner_manifest import RunnerManifest

compact_runner = {
    "kind": "TestRunner",
}


def test_manifest_should_accept_minimum_runner():
    # Arrange
    data = compact_runner

    # Act
    RunnerManifest(**data)

    # Assert
    assert True


def test_manifest_should_reject_runner_without_kind():
    # Arrange
    data = deepcopy(compact_runner)
    del data["kind"]

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
    data = deepcopy(compact_runner)
    data[field_name] = field_value

    # Act
    manifest = RunnerManifest(**data)

    # Assert
    assert getattr(manifest, field_name) == field_value


@pytest.mark.parametrize(
    "field_name,invalid_value",
    [
        ("kind", 123),
        ("name", 456),
        ("description", 789),
        ("streaming", "not_a_bool"),
    ],
)
def test_manifest_should_reject_runner_with_invalid_field_types(field_name, invalid_value):
    # Arrange
    data = deepcopy(compact_runner)
    data[field_name] = invalid_value

    # Act
    with pytest.raises(ValidationError):
        RunnerManifest(**data)


def test_manifest_should_have_correct_defaults():
    # Arrange
    data = compact_runner

    # Act
    manifest = RunnerManifest(**data)

    # Assert
    assert manifest.name is None
    assert manifest.description is None
    assert manifest.streaming is False
