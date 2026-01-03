from copy import deepcopy

import pytest
from pydantic import ValidationError

from tests.mocks.manifests.mini import compact_job
from tiozin.api.metadata.job_manifest import (
    JobManifest,
)


def test_manifest_should_accept_minimum_job():
    # Arrange
    data = compact_job

    # Act
    JobManifest(**data)

    # Assert
    assert True


@pytest.mark.parametrize(
    "field_to_remove",
    ["kind", "name", "org", "region", "domain", "product", "model", "layer", "runner", "inputs"],
)
def test_manifest_should_reject_job_without_required_field(field_to_remove):
    # Arrange
    data = deepcopy(compact_job)
    del data[field_to_remove]

    # Act
    with pytest.raises(ValidationError):
        JobManifest(**data)


def test_manifest_should_reject_job_with_empty_inputs_list():
    # Arrange
    data = deepcopy(compact_job)
    data["inputs"] = []

    # Act
    with pytest.raises(ValidationError):
        JobManifest(**data)


def test_manifest_should_accept_job_with_empty_optional_lists():
    # Arrange
    data = deepcopy(compact_job)
    data["transforms"] = []
    data["outputs"] = []

    # Act
    manifest = JobManifest(**data)

    # Assert
    assert manifest.transforms == []
    assert manifest.outputs == []


@pytest.mark.parametrize(
    "field_name,field_value",
    [
        ("owner", "team@example.com"),
        ("maintainer", "dev@example.com"),
        ("cost_center", "CC-12345"),
        ("description", "A test job description"),
        ("labels", {"env": "test", "version": "1.0"}),
    ],
)
def test_manifest_should_accept_job_with_optional_fields(field_name, field_value):
    # Arrange
    data = deepcopy(compact_job)
    data[field_name] = field_value

    # Act
    manifest = JobManifest(**data)

    # Assert
    assert getattr(manifest, field_name) == field_value


@pytest.mark.parametrize(
    "field_name,invalid_value",
    [
        ("kind", 123),
        ("name", 456),
        ("labels", "not_a_dict"),
        ("inputs", "not_a_list"),
        ("runner", "not_a_dict"),
    ],
)
def test_manifest_should_reject_job_with_invalid_field_types(field_name, invalid_value):
    # Arrange
    data = deepcopy(compact_job)
    data[field_name] = invalid_value

    # Act
    with pytest.raises(ValidationError):
        JobManifest(**data)


def test_manifest_should_have_correct_defaults():
    # Arrange
    data = deepcopy(compact_job)
    # Remove optional fields to test defaults
    data.pop("transforms", None)
    data.pop("outputs", None)

    # Act
    manifest = JobManifest(**data)

    # Assert
    assert manifest.transforms == []
    assert manifest.outputs == []
    assert manifest.labels == {}
    assert manifest.description is None
    assert manifest.owner is None
    assert manifest.maintainer is None
    assert manifest.cost_center is None


def test_manifest_should_accept_multiple_pipeline_components():
    # Arrange
    data = deepcopy(compact_job)
    data["inputs"] = [
        {"kind": "TestInput", "name": "input_1"},
        {"kind": "TestInput", "name": "input_2"},
        {"kind": "TestInput", "name": "input_3"},
    ]
    data["transforms"] = [
        {"kind": "TestTransform", "name": "transform_1"},
        {"kind": "TestTransform", "name": "transform_2"},
    ]
    data["outputs"] = [
        {"kind": "TestOutput", "name": "output_1"},
        {"kind": "TestOutput", "name": "output_2"},
    ]

    # Act
    manifest = JobManifest(**data)

    # Assert
    assert len(manifest.inputs) == 3
    assert len(manifest.transforms) == 2
    assert len(manifest.outputs) == 2
