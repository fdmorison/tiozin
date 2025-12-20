from copy import deepcopy

from pydantic import ValidationError
import pytest

from tests.mocks.manifests.mini import compact_job
from tio.registries.job.model import (
    InputManifest,
    JobManifest,
)


def test_manifest_should_accept_minimum_job():
    # Arrange
    data = compact_job

    # Act
    JobManifest(**data)

    # Assert
    assert True


def test_manifest_should_reject_job_without_name():
    # Arrange
    data = deepcopy(compact_job)
    del data["name"]

    # Act
    with pytest.raises(ValidationError):
        JobManifest(**data)


def test_manifest_should_reject_job_without_kind():
    # Arrange
    data = deepcopy(compact_job)
    del data["kind"]

    # Act
    with pytest.raises(ValidationError):
        JobManifest(**data)


def test_manifest_should_reject_job_without_taxonomy():
    # Arrange
    data = deepcopy(compact_job)
    del data["org"]
    del data["region"]
    del data["domain"]
    del data["product"]
    del data["model"]
    del data["layer"]

    # Act
    with pytest.raises(ValidationError):
        JobManifest(**data)


def test_manifest_should_reject_job_without_steps():
    # Arrange
    data = deepcopy(compact_job)
    data["inputs"] = {}
    data["transforms"] = {}
    data["outputs"] = {}

    # Act & Assert
    with pytest.raises(ValidationError, match="Job must have at least one Input step"):
        JobManifest(**data)


def test_manifest_should_accept_job_with_input_step_only():
    # Arrange
    data = deepcopy(compact_job)
    data["transforms"] = {}
    data["outputs"] = {}

    # Act
    manifest = JobManifest(**data)

    # Assert
    actual = {
        **manifest.inputs,
        **manifest.transforms,
        **manifest.outputs,
    }
    expected = {
        "read_something": InputManifest(kind="TestInput"),
    }
    assert actual == expected


def test_manifest_should_reject_job_with_transform_step_only():
    # Arrange
    data = deepcopy(compact_job)
    data["inputs"] = {}
    data["outputs"] = {}

    # Act
    with pytest.raises(ValidationError, match="Job must have at least one Input step"):
        JobManifest(**data)


def test_manifest_should_reject_job_with_output_step_only():
    # Arrange
    data = deepcopy(compact_job)
    data["inputs"] = {}
    data["transforms"] = {}

    # Act
    with pytest.raises(ValidationError, match="Job must have at least one Input step"):
        JobManifest(**data)
