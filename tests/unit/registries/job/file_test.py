import json
from pathlib import Path
from textwrap import dedent

import pytest

from tests.mocks.manifests import mini
from tiozin.api import JobManifest
from tiozin.exceptions import JobManifestError
from tiozin.family.tio_kernel import FileJobRegistry


def test_get_should_load_yaml_manifest_from_local_file():
    # Arrange
    path = "tests/mocks/manifests/mini.yaml"

    # Act
    manifest = FileJobRegistry().get(path)

    # Assert
    actual = manifest.model_dump()
    expected = mini.expanded_job
    assert actual == expected


def test_get_should_load_json_manifest_from_local_file():
    # Arrange
    path = "tests/mocks/manifests/mini.json"

    # Act
    manifest = FileJobRegistry().get(path)

    # Assert
    actual = manifest.model_dump()
    expected = mini.expanded_job
    assert actual == expected


def test_get_should_fail_when_manifest_has_duplicated_keys():
    # Arrange
    path = "tests/mocks/manifests/duplicated_key.yaml"

    # Act
    with pytest.raises(JobManifestError, match="duplicate key"):
        FileJobRegistry().get(path)


def test_get_should_fail_on_schema_validation_error():
    # Arrange
    path = "tests/mocks/manifests/invalid_schema.yaml"

    # Act
    with pytest.raises(JobManifestError, match="The provided TransformManifest cannot be parsed"):
        FileJobRegistry().get(path)


def test_register_should_write_yaml_manifest(tmp_path: Path):
    # Arrange
    path = tmp_path / "job.yaml"
    manifest = JobManifest(**mini.expanded_job)

    # Act
    FileJobRegistry().register(path, manifest)

    # Assert
    actual = path.read_text(encoding="utf8")
    expected = dedent(
        """
      kind: Job
      name: test_job
      org: tiozin
      region: latam
      domain: quality
      product: test_cases
      model: some_case
      layer: test
      labels: {}
      runner:
        kind: TestRunner
        streaming: false
      inputs:
      - kind: TestInput
        name: read_something
      transforms:
      - kind: TestTransform
        name: transform_something
      outputs:
      - kind: TestOutput
        name: write_something
    """
    ).lstrip()
    assert actual == expected


def test_register_should_write_json_manifest(tmp_path: Path):
    # Arrange
    path = tmp_path / "job.json"
    manifest = JobManifest(**mini.expanded_job)

    # Act
    FileJobRegistry().register(path, manifest)

    # Assert
    actual = json.loads(path.read_text())
    expected = manifest.model_dump(exclude_none=True)
    assert actual == expected
