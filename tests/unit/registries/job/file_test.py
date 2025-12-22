import json
from pathlib import Path
from textwrap import dedent

import pytest

from tests.mocks.manifests import mini
from tiozin.family.tio_kernel.registries.file_job_registry import FileJobRegistry, JobManifest


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
    with pytest.raises(Exception, match="duplicate key"):
        FileJobRegistry().get(path)


def test_get_should_fail_on_schema_validation_error():
    # Arrange
    path = "tests/mocks/manifests/invalid_schema.yaml"

    # Act
    with pytest.raises(Exception, match="The provided TransformManifest cannot be parsed"):
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
      org: tiozin
      region: latam
      domain: quality
      product: test_cases
      model: some_case
      layer: test
      name: test_job
      labels: {}
      runner:
        kind: TestRunner
        streaming: false
      inputs:
        read_something:
          kind: TestInput
      transforms:
        transform_something:
          kind: TestTransform
      outputs:
        write_something:
          kind: TestOutput
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
