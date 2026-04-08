from pathlib import Path

import pytest

from tiozin.api.metadata.job.model import (
    InputManifest,
    JobManifest,
    OutputManifest,
    RunnerManifest,
    TransformManifest,
)
from tiozin.exceptions import JobNotFoundError
from tiozin.family.tio_kernel import FileJobRegistry


# ============================================================================
# Access Tests
# ============================================================================
def test_get_should_read_from_public_s3_bucket():
    # Arrange
    path = "s3://1000genomes/i_dont_exist.yaml"

    # Act/Assert
    with pytest.raises(JobNotFoundError):
        FileJobRegistry(anon=True).get(path)


# ============================================================================
# Read tests
# ============================================================================


@pytest.mark.parametrize("ext", ["json", "yaml"])
def test_get_should_load_manifest_from_local_file(ext: str):
    # Arrange
    path = f"tests/mocks/jobs/default_job.{ext}"

    # Act
    manifest = FileJobRegistry().get(path)

    # Assert
    actual = manifest
    expected = JobManifest(
        kind="LinearJob",
        name="default_job",
        org="tiozin",
        region="latam",
        domain="data",
        subdomain="platform",
        product="noop",
        model="noop",
        layer="refined",
        runner=RunnerManifest(kind="NoOpRunner"),
        inputs=[InputManifest(kind="NoOpInput", name="noop_input")],
        transforms=[TransformManifest(kind="NoOpTransform", name="noop_transform")],
        outputs=[OutputManifest(kind="NoOpOutput", name="noop_output")],
    )
    assert actual == expected


# ============================================================================
# location as base directory
# ============================================================================


@pytest.mark.parametrize("ext", ["json", "yaml"])
def test_get_should_load_manifest_when_identifier_is_relative_to_location(ext: str):
    # Arrange
    registry = FileJobRegistry(location="tests/mocks/jobs")

    # Act
    manifest = registry.get(f"default_job.{ext}")

    # Assert
    actual = manifest.name
    expected = "default_job"
    assert actual == expected


@pytest.mark.parametrize("ext", ["json", "yaml"])
def test_get_should_load_manifest_when_identifier_is_absolute_and_location_is_set(ext: str):
    # Arrange
    abs_path = str(Path(f"tests/mocks/jobs/default_job.{ext}").resolve())
    registry = FileJobRegistry(location="tests/mocks/jobs")

    # Act
    manifest = registry.get(abs_path)

    # Assert
    actual = manifest.name
    expected = "default_job"
    assert actual == expected


@pytest.mark.parametrize("ext", ["json", "yaml"])
def test_register_should_write_to_location_when_identifier_is_relative(ext: str, tmp_path: Path):
    # Arrange
    manifest = JobManifest(
        kind="LinearJob",
        name="default_job",
        org="tiozin",
        region="latam",
        domain="data",
        subdomain="platform",
        product="noop",
        model="noop",
        layer="refined",
        runner=RunnerManifest(kind="NoOpRunner"),
        inputs=[InputManifest(kind="NoOpInput", name="noop_input")],
        transforms=[TransformManifest(kind="NoOpTransform", name="noop_transform")],
        outputs=[OutputManifest(kind="NoOpOutput", name="noop_output")],
    )
    registry = FileJobRegistry(location=str(tmp_path))

    # Act
    registry.register(f"job.{ext}", manifest)

    # Assert
    actual = (tmp_path / f"job.{ext}").read_text(encoding="utf8")
    expected = Path(f"tests/mocks/jobs/default_job.{ext}").read_text(encoding="utf8")
    assert actual == expected


# ============================================================================
# Write tests
# ============================================================================


@pytest.mark.parametrize("ext", ["json", "yaml"])
def test_register_should_write_manifest_to_local_file(ext: str, tmp_path: Path):
    # Arrange
    output_path = tmp_path / f"job.{ext}"
    manifest = JobManifest(
        kind="LinearJob",
        name="default_job",
        org="tiozin",
        region="latam",
        domain="data",
        subdomain="platform",
        product="noop",
        model="noop",
        layer="refined",
        runner=RunnerManifest(kind="NoOpRunner"),
        inputs=[InputManifest(kind="NoOpInput", name="noop_input")],
        transforms=[TransformManifest(kind="NoOpTransform", name="noop_transform")],
        outputs=[OutputManifest(kind="NoOpOutput", name="noop_output")],
    )

    # Act
    FileJobRegistry().register(str(output_path), manifest)

    # Assert
    actual = output_path.read_text(encoding="utf8")
    expected = Path(f"tests/mocks/jobs/default_job.{ext}").read_text(encoding="utf8")
    assert actual == expected
