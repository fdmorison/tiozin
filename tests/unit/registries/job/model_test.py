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
